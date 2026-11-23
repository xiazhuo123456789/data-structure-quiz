# 安卓版构建说明

这是“数据结构刷题系统”的安卓外壳。它用原生 `WebView` 加载 `assets/index.html`，不依赖在线页面，不需要网络权限。

## 版本信息

| 项目 | 值 |
| --- | --- |
| 应用名称 | 数据结构刷题系统 |
| 包名 | `com.xiazhuo.datastructurequiz` |
| 版本名 | `1.2.5` |
| 版本号 | `10205` |
| 最低系统 | Android 8.0（API 26） |
| 目标系统 | Android 14（API 34） |
| 编译 SDK | Android 15（API 35） |
| 权限 | 无 |
| 页面来源 | `file:///android_asset/index.html` |

## 目录

```text
android/
├─ app/
│  ├─ build.gradle                 # 包名、版本、签名
│  └─ src/main/
│     ├─ AndroidManifest.xml
│     ├─ assets/index.html         # 由 build_android.py 生成
│     ├─ java/.../MainActivity.java
│     └─ res/                      # 图标、启动页、主题
├─ tools/
│  ├─ build_android.py             # 复制桌面单文件页面到 assets
│  └─ make_android_icons.py        # 生成各密度图标
├─ build.gradle
├─ settings.gradle
├─ gradle.properties
├─ gradle/wrapper/
└─ gradlew.bat
```

## 构建环境

- JDK 17
- Android SDK Platform 35
- Android Build-Tools 35.0.0
- Gradle 8.9
- Android Gradle Plugin 8.7.3

`local.properties` 指向本机 SDK：

```properties
sdk.dir=E:/Android/Sdk
```

这个文件只在本机使用，不要提交。

## 发布签名

在 `android/keystore.properties` 写入：

```properties
storePassword=你的口令
keyPassword=你的口令
keyAlias=datastructurequiz
storeFile=release-key.jks
```

`release-key.jks` 和 `keystore.properties` 都已经加入 `.gitignore`。升级安装必须继续用同一个密钥签名，否则手机会拒绝覆盖安装。请自行备份这两个文件。

## 编译

```powershell
cd android
python tools/build_android.py
gradle assembleRelease
```

也可以使用项目自带的 wrapper：

```powershell
.\gradlew.bat assembleRelease
```

wrapper 首次运行会下载 Gradle 8.9，网络慢时可以先在本机安装 Gradle，或者把 `gradle/wrapper/gradle-wrapper.properties` 的地址换成可用镜像。

产物：

```text
android/app/build/outputs/apk/release/app-release.apk
```

## 检查

```powershell
# 签名
E:\Android\Sdk\build-tools\35.0.0\apksigner.bat verify --verbose app-release.apk

# 包名、版本、权限
E:\Android\Sdk\build-tools\35.0.0\aapt2.exe dump badging app-release.apk
E:\Android\Sdk\build-tools\35.0.0\aapt2.exe dump permissions app-release.apk
```

## 行为说明

- 返回键：网页有历史时后退；没有历史时退到桌面，不直接杀进程。
- 外部链接：GitHub 等 `http/https` 链接交给系统浏览器打开。
- 导入题库：点“导入 JSON 题库”会打开系统文件选择器，选中 JSON 后由页面读取并替换题库。
- 导出题库：点“导出当前题库”会打开系统“另存为”面板，直接保存 JSON，不需要存储权限。
- 页面滚动、输入框和 `localStorage` 都由 WebView 自己处理。
- 应用锁定竖屏，避免答题页在横屏下过矮。
- 不申请网络权限，也不申请存储权限。

## 已知限制

- APK 使用自签名证书，不上架应用商店。安装时 Android 会提示未知来源。
- 卸载应用会清除 WebView 里的答题记录。
- 桌面版和安卓版的记录不互通。
- 文件选择器和“另存为”面板由手机系统提供，不同手机的样式会不一样。
