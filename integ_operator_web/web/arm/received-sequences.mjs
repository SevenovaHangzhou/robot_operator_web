// Loading received sequences reads data only. Only the existing Play button sends a command.
export class ReceivedSequences {
  constructor(read, now = () => Date.now() / 1000, random = () => {
    const bytes = new Uint8Array(16); crypto.getRandomValues(bytes);
    return Array.from(bytes, x => x.toString(16).padStart(2, '0')).join('');
  }) { this.read = read; this.now = now; this.random = random; this.rows = []; this.loaded = null; this.fresh = false; }
  async refresh() {
    this.fresh = false;
    const result = await this.read('/api/arm/experiment-packages');
    this.rows = result.packages; this.capabilities = result.capabilities; this.fresh = true;
    return this.rows;
  }
  reason(row) {
    if (!this.fresh) return '接收状态未更新';
    if (!this.capabilities.execution_enabled) return '接收端配置未就绪';
    if (!row) return '请选择收到的动作序列';
    if (row.revoked) return '已撤回';
    if (row.attempt) return row.attempt.state === 'complete' ? '已执行完毕' : '已有执行记录，请对账';
    if (row.expires_at <= this.now()) return '已过期，请在18141撤回后重新下发';
    return '';
  }
  async load(id, status, info) {
    if (!status || !info) throw new Error('请先连接并等待机械臂状态');
    if (status.sequence || status.moving) throw new Error('运动中不能载入动作序列');
    await this.refresh();
    const row = this.rows.find(r => r.package_id === id), reason = this.reason(row);
    if (reason) throw new Error(reason);
    const result = await this.read('/api/arm/experiment-packages/' + encodeURIComponent(id));
    if (result.package_id !== id || result.sha256 !== row.sha256 || result.motion_started !== false ||
        result.expires_at <= this.now() || !Array.isArray(result.steps) || result.steps.length !== row.total ||
        !result.steps.every(s => info.gears.some(g => g.name === s.gear))) throw new Error('载入内容或档位与接收记录不一致');
    this.loaded = Object.freeze({...result, request_id: this.random()});
    return this.loaded;
  }
  command() {
    const loaded = this.loaded;
    if (!loaded) throw new Error('请先载入动作序列');
    const reason = this.reason(this.rows.find(r => r.package_id === loaded.package_id));
    if (reason) throw new Error(reason);
    return {package_id: loaded.package_id, request_id: loaded.request_id};
  }
  clear() { this.loaded = null; }
}

export function receivedSequencesUI({state, render, toast, read = async path => {
  const response = await fetch(path, {cache:'no-store'});
  if (!response.ok) {
    if (response.status === 404) throw new Error('当前操作台未启用18141接收端');
    if (response.status === 401) throw new Error('登录后自动读取收到的动作序列');
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error || `HTTP ${response.status}`);
  }
  return response.json();
}}) {
  const $ = id => document.getElementById(id), model = new ReceivedSequences(read);
  const select = $('received-select'), load = $('received-load'), note = $('received-status');
  let busy = false;
  function update() {
    load.disabled = busy || !state.status || Boolean(state.status.sequence || state.status.moving) ||
      Boolean(model.reason(model.rows.find(r => r.package_id === select.value)));
  }
  async function refresh() {
    if (busy) return;
    busy = true; update();
    try {
      const previous = select.value, rows = await model.refresh();
      const placeholder = document.createElement('option'); placeholder.value = ''; placeholder.textContent = '选择18141发来的动作序列';
      select.replaceChildren(placeholder, ...rows.map(row => {
        const option = document.createElement('option'), why = model.reason(row);
        option.value = row.package_id; option.textContent = `${row.preset_id} · ${row.total}段${why ? ' · '+why : ''}`;
        option.disabled = Boolean(why); return option;
      }));
      select.value = rows.some(r => r.package_id === previous) ? previous : '';
      note.textContent = state.experimentPackage ? `已载入 ${state.experimentPackage.preset_id}；目标、速度和停留已冻结，核对后点击“播放收到的序列”。` :
        rows.length ? `已接收${rows.length}个动作包。选择后载入，仅准备列表，不运动。` : '暂无收到的动作序列；从18141执行区发送已审核批次。';
    } catch (error) { note.textContent = error.message; }
    finally { busy = false; update(); render(); }
  }
  load.addEventListener('click', async () => {
    if (busy) return; busy = true; update();
    const previousLoaded = model.loaded;
    try {
      const loaded = await model.load(select.value,state.status,state.info);
      // State may change while the read is in flight.
      if (!state.status || state.status.sequence || state.status.moving) {model.loaded = previousLoaded;throw new Error('状态已变化，请停止后重新载入');}
      state.experimentPackage = loaded;
      state.sequence = loaded.steps.map(({name,gear,dwell_s}) => ({name,gear,dwell_s}));
      note.textContent = `已载入 ${loaded.preset_id}；${loaded.steps.length}段。核对后点击“播放收到的序列”。`;
      toast('已载入收到的序列，尚未运动');
    } catch (error) { toast(error.message,true); }
    finally { busy = false; update(); render(); }
  });
  select.addEventListener('change', update);
  $('received-refresh').addEventListener('click', refresh);
  // Polling updates the catalog, never loads a sequence or starts motion.
  const timer = setInterval(refresh,5000); void refresh();
  window.addEventListener('pagehide',() => clearInterval(timer),{once:true});
  return {model,update,refresh};
}
