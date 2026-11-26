const { app, BrowserWindow, Menu, shell, dialog } = require('electron');
const path = require('path');
const fs = require('fs');

const APP_NAME = '研题台';
const GITHUB_URL = 'https://github.com/xiazhuo123456789';

app.setName(APP_NAME);
app.setAppUserModelId('com.xiazhuo.datastructurequiz');

// 旧版 1.2.x 的用户目录叫“数据结构刷题系统”。首启时复制一份到新目录，
// 避免答题记录、题库和窗口位置丢失；旧目录保留，不删除。
(function migrateLegacyUserData(){
  if(!app.isPackaged) return;
  try{
    const appData = app.getPath('appData');
    const legacyDir = path.join(appData, '数据结构刷题系统');
    const currentDir = path.join(appData, APP_NAME);
    if(fs.existsSync(legacyDir) && !fs.existsSync(currentDir)){
      fs.cpSync(legacyDir, currentDir, { recursive: true });
    }
  }catch(e){
    // 迁移失败不阻塞启动，最多回到全新记录。
  }
})();

let mainWindow = null;
let saveTimer = null;

function statePath() {
  return path.join(app.getPath('userData'), 'window-state.json');
}

function readState() {
  try {
    return JSON.parse(fs.readFileSync(statePath(), 'utf8'));
  } catch {
    return {};
  }
}

function saveState() {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  if (mainWindow.isMaximized() || mainWindow.isFullScreen()) return;
  try {
    const bounds = mainWindow.getNormalBounds();
    fs.mkdirSync(path.dirname(statePath()), { recursive: true });
    fs.writeFileSync(statePath(), JSON.stringify(bounds), 'utf8');
  } catch {
    /* 窗口尺寸只是锦上添花，写失败不影响使用 */
  }
}

function scheduleSave() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(saveState, 500);
}

function createWindow() {
  const state = readState();
  mainWindow = new BrowserWindow({
    width: Math.max(980, Number(state.width) || 1280),
    height: Math.max(660, Number(state.height) || 880),
    x: Number.isFinite(state.x) ? state.x : undefined,
    y: Number.isFinite(state.y) ? state.y : undefined,
    minWidth: 940,
    minHeight: 640,
    show: false,
    backgroundColor: '#f4f2ea',
    title: APP_NAME,
    icon: path.join(__dirname, '..', 'assets', 'icon.png'),
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      spellcheck: false
    }
  });

  mainWindow.loadFile(path.join(__dirname, '..', 'app', 'index.html'));
  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.on('resize', scheduleSave);
  mainWindow.on('move', scheduleSave);
  mainWindow.on('close', saveState);
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // 所有外部链接都交给系统浏览器，应用窗口本身不跳走。
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (url === mainWindow.webContents.getURL()) return;
    event.preventDefault();
    if (/^https?:\/\//i.test(url)) shell.openExternal(url);
  });
}

function showAbout() {
  dialog.showMessageBox(mainWindow, {
    type: 'info',
    title: '关于',
    message: APP_NAME,
    detail: `版本 ${app.getVersion()}\n多学科题库 + DeepSeek AI 助教\n考试模式 / 作业模式 / 错题本 / 练习记录 / 题库导入导出 / AI 问答\n\nGitHub：${GITHUB_URL}`,
    buttons: ['确定']
  });
}

function buildMenu() {
  const template = [
    {
      label: '文件',
      submenu: [
        {
          label: '重新加载',
          accelerator: 'CmdOrCtrl+R',
          click: () => mainWindow && mainWindow.reload()
        },
        { type: 'separator' },
        { label: '退出', accelerator: 'Alt+F4', role: 'quit' }
      ]
    },
    {
      label: '视图',
      submenu: [
        { label: '全屏', accelerator: 'F11', role: 'togglefullscreen' },
        { label: '放大', accelerator: 'CmdOrCtrl+=', role: 'zoomIn' },
        { label: '缩小', accelerator: 'CmdOrCtrl+-', role: 'zoomOut' },
        { label: '实际大小', accelerator: 'CmdOrCtrl+0', role: 'resetZoom' }
      ]
    },
    {
      label: '帮助',
      submenu: [
        {
          label: '访问 GitHub 主页',
          click: () => shell.openExternal(GITHUB_URL)
        },
        { label: '关于', click: showAbout }
      ]
    }
  ];

  if (process.platform === 'darwin') template.unshift({ role: 'appMenu' });
  return Menu.buildFromTemplate(template);
}

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (!mainWindow) return;
    if (mainWindow.isMinimized()) mainWindow.restore();
    if (!mainWindow.isVisible()) mainWindow.show();
    mainWindow.focus();
  });

  app.whenReady().then(() => {
    Menu.setApplicationMenu(buildMenu());
    createWindow();
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
  });
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
