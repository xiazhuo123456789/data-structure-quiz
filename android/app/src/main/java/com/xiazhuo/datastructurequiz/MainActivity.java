package com.xiazhuo.datastructurequiz;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

/**
 * 单 Activity 的 WebView 外壳。
 *
 * 页面、题库、样式和脚本全部放在 assets/index.html 内。
 * 不加载远程页面；AI 问答按需访问 DeepSeek，答题记录仍由页面写入 WebView 的 localStorage。
 */
public class MainActivity extends Activity {

    private static final String START_URL = "file:///android_asset/index.html";
    private static final int REQ_PICK_JSON = 1001;
    private static final int REQ_EXPORT_JSON = 1002;
    private WebView webView;
    private TextView loadingView;
    private ValueCallback<Uri[]> pendingFileCallback;
    private String pendingExportText;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getWindow().setStatusBarColor(Color.rgb(7, 16, 14));
        getWindow().setNavigationBarColor(Color.rgb(7, 16, 14));

        webView = new WebView(this);
        webView.setBackgroundColor(Color.rgb(7, 16, 14));
        webView.setOverScrollMode(View.OVER_SCROLL_NEVER);
        webView.setVerticalScrollBarEnabled(false);
        webView.setHorizontalScrollBarEnabled(false);

        loadingView = new TextView(this);
        loadingView.setText("研题台\n正在加载题库…");
        loadingView.setTextColor(Color.rgb(231, 241, 236));
        loadingView.setTextSize(16);
        loadingView.setGravity(Gravity.CENTER);
        loadingView.setLineSpacing(0, 1.4f);
        loadingView.setBackgroundColor(Color.rgb(7, 16, 14));

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(7, 16, 14));
        root.addView(webView, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT));
        root.addView(loadingView, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT));
        setContentView(root);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setSupportMultipleWindows(false);
        settings.setGeolocationEnabled(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);

        webView.addJavascriptInterface(new ExportBridge(), "AndroidExport");
        webView.setWebChromeClient(new LocalChromeClient());
        webView.setWebViewClient(new LocalWebViewClient());

        boolean debuggable = (getApplicationInfo().flags & ApplicationInfo.FLAG_DEBUGGABLE) != 0;
        WebView.setWebContentsDebuggingEnabled(debuggable);

        boolean restored = false;
        if (savedInstanceState != null) {
            restored = webView.restoreState(savedInstanceState) != null;
        }
        if (!restored) {
            webView.loadUrl(START_URL);
        }
    }

    /**
     * 让题库页的 <input type="file"> 能真正打开系统文件选择器。
     */
    private final class LocalChromeClient extends WebChromeClient {
        @Override
        public boolean onShowFileChooser(
                WebView view,
                ValueCallback<Uri[]> filePathCallback,
                FileChooserParams fileChooserParams) {
            if (pendingFileCallback != null) {
                pendingFileCallback.onReceiveValue(null);
            }
            pendingFileCallback = filePathCallback;

            String mime = "*/*";
            String[] acceptTypes = fileChooserParams == null ? null : fileChooserParams.getAcceptTypes();
            if (acceptTypes != null) {
                for (String type : acceptTypes) {
                    if (type != null && type.contains("/")) {
                        mime = type;
                        break;
                    }
                }
            }

            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            intent.setType(mime);
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            if ("*/*".equals(mime)) {
                intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{"application/json", "text/plain"});
            }

            try {
                startActivityForResult(intent, REQ_PICK_JSON);
                return true;
            } catch (ActivityNotFoundException ignored) {
                pendingFileCallback = null;
                Toast.makeText(MainActivity.this, "手机上没有可用的文件选择器", Toast.LENGTH_SHORT).show();
                return false;
            }
        }
    }

    /**
     * 页面导出题库时，交给系统“另存为”面板，避免 WebView 无法下载 blob。
     */
    private final class ExportBridge {
        @JavascriptInterface
        public void saveJson(final String filename, final String text) {
            runOnUiThread(() -> {
                if (pendingExportText != null) {
                    Toast.makeText(MainActivity.this, "请先完成上一次导出", Toast.LENGTH_SHORT).show();
                    return;
                }
                pendingExportText = text;

                Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("application/json");
                intent.putExtra(Intent.EXTRA_TITLE, filename);

                try {
                    startActivityForResult(intent, REQ_EXPORT_JSON);
                } catch (ActivityNotFoundException ignored) {
                    pendingExportText = null;
                    Toast.makeText(MainActivity.this, "手机上没有可用的保存面板", Toast.LENGTH_SHORT).show();
                }
            });
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (requestCode == REQ_PICK_JSON) {
            ValueCallback<Uri[]> callback = pendingFileCallback;
            pendingFileCallback = null;
            if (callback == null) {
                return;
            }
            Uri uri = (resultCode == RESULT_OK && data != null) ? data.getData() : null;
            callback.onReceiveValue(uri == null ? null : new Uri[]{uri});
            return;
        }

        if (requestCode == REQ_EXPORT_JSON) {
            String text = pendingExportText;
            pendingExportText = null;
            if (resultCode != RESULT_OK || data == null || data.getData() == null || text == null) {
                return;
            }
            try (OutputStream out = getContentResolver().openOutputStream(data.getData())) {
                if (out == null) {
                    throw new IllegalStateException("无法写入所选位置");
                }
                out.write(text.getBytes(StandardCharsets.UTF_8));
                Toast.makeText(this, "题库已导出", Toast.LENGTH_SHORT).show();
            } catch (Exception e) {
                Toast.makeText(this, "导出失败，请换一个保存位置", Toast.LENGTH_SHORT).show();
            }
        }
    }

    private final class LocalWebViewClient extends WebViewClient {
        @Override
        public void onPageStarted(WebView view, String url, Bitmap favicon) {
            super.onPageStarted(view, url, favicon);
            if (loadingView != null) {
                loadingView.setText("研题台\n正在加载题库…");
                loadingView.setVisibility(View.VISIBLE);
            }
        }

        @Override
        public void onPageFinished(WebView view, String url) {
            super.onPageFinished(view, url);
            if (loadingView != null && url != null && url.startsWith(START_URL)) {
                loadingView.post(() -> {
                    if (loadingView != null) {
                        loadingView.setVisibility(View.GONE);
                    }
                });
            }
        }

        @Override
        public void onReceivedError(
                WebView view,
                WebResourceRequest request,
                WebResourceError error) {
            super.onReceivedError(view, request, error);
            if (loadingView != null && request != null && request.isForMainFrame()) {
                loadingView.setText("页面加载失败\n请退出应用后重新打开");
                loadingView.setVisibility(View.VISIBLE);
            }
        }

        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            return openExternally(request.getUrl());
        }

        @Override
        @SuppressWarnings("deprecation")
        public boolean shouldOverrideUrlLoading(WebView view, String url) {
            return openExternally(Uri.parse(url));
        }

        /**
         * 返回 true 表示已交给系统处理，WebView 不再跳转。
         */
        private boolean openExternally(Uri uri) {
            if (uri == null) {
                return false;
            }
            String scheme = uri.getScheme();
            if (scheme == null) {
                return false;
            }
            // assets 内部页面、页内锚点和脚本地址仍由 WebView 自己处理
            if (scheme.equalsIgnoreCase("file")
                    || scheme.equalsIgnoreCase("about")
                    || scheme.equalsIgnoreCase("javascript")
                    || scheme.equalsIgnoreCase("data")
                    || scheme.equalsIgnoreCase("blob")) {
                return false;
            }
            if (scheme.equalsIgnoreCase("http")
                    || scheme.equalsIgnoreCase("https")
                    || scheme.equalsIgnoreCase("mailto")
                    || scheme.equalsIgnoreCase("tel")) {
                try {
                    Intent intent = new Intent(Intent.ACTION_VIEW, uri);
                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    startActivity(intent);
                } catch (ActivityNotFoundException ignored) {
                    // 设备没有可处理该链接的应用时，安静返回，避免闪退
                }
                return true;
            }
            return false;
        }
    }

    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
            return;
        }
        // 页面没有历史记录时，退到桌面，保留后台状态
        moveTaskToBack(true);
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        if (webView != null) {
            webView.saveState(outState);
        }
    }

    @Override
    protected void onDestroy() {
        if (pendingFileCallback != null) {
            pendingFileCallback.onReceiveValue(null);
            pendingFileCallback = null;
        }
        pendingExportText = null;
        if (webView != null) {
            webView.stopLoading();
            webView.loadUrl("about:blank");
            webView.removeAllViews();
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }
}

