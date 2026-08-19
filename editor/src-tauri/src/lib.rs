use std::{fs, path::{Path, PathBuf}};
use tauri::Emitter;

fn allowed_file(path: &Path) -> bool {
    matches!(path.extension().and_then(|v| v.to_str()), Some("json") | Some("md") | Some("markdown"))
}

#[tauri::command]
fn read_text_file(path: String) -> Result<String, String> {
    let path = PathBuf::from(path);
    if !allowed_file(&path) { return Err("Only JSON and Markdown files can be opened".into()); }
    fs::read_to_string(path).map_err(|e| e.to_string())
}

#[tauri::command]
fn write_text_file(path: String, content: String) -> Result<(), String> {
    let path = PathBuf::from(path);
    if !allowed_file(&path) { return Err("Only JSON and Markdown files can be saved".into()); }
    fs::write(path, content).map_err(|e| e.to_string())
}

fn collect_files(dir: &Path, result: &mut Vec<String>) {
    let Ok(entries) = fs::read_dir(dir) else { return };
    for entry in entries.flatten() {
        let path = entry.path();
        if path.file_name().and_then(|v| v.to_str()).is_some_and(|v| matches!(v, ".git" | "node_modules" | "dist" | "target" | "__pycache__")) { continue; }
        if path.is_dir() { collect_files(&path, result); }
        else if allowed_file(&path) { result.push(path.to_string_lossy().to_string()); }
    }
}

#[tauri::command]
fn list_files(root: String) -> Result<Vec<String>, String> {
    let root = PathBuf::from(root);
    if !root.is_dir() { return Err("Selected project folder is not a directory".into()); }
    let mut files = Vec::new(); collect_files(&root, &mut files); files.sort(); Ok(files)
}

#[derive(serde::Serialize)]
struct CheckResult { ok: bool, keys: usize, message: String }

#[tauri::command]
fn check_i18n_consistency(root: String) -> Result<CheckResult, String> {
    let base = PathBuf::from(root).join("src/data/i18n");
    let codes = ["ja", "en", "zh-Hans", "zh-TW"];
    let mut docs: Vec<(String, serde_json::Map<String, serde_json::Value>)> = Vec::new();
    for code in codes {
        let path = base.join(format!("{code}.json"));
        if !path.exists() { continue; }
        let content = fs::read_to_string(&path).map_err(|e| e.to_string())?;
        let value: serde_json::Value = serde_json::from_str(&content).map_err(|e| format!("{code}.json: {e}"))?;
        if let Some(object) = value.as_object() { docs.push((code.into(), object.clone())); }
    }
    if docs.is_empty() { return Ok(CheckResult { ok: false, keys: 0, message: "No i18n JSON files found under src/data/i18n".into() }); }
    let all: std::collections::BTreeSet<String> = docs.iter().flat_map(|(_, map)| map.keys().cloned()).collect();
    let missing: Vec<String> = docs.iter().filter_map(|(lang, map)| {
        let absent: Vec<_> = all.iter().filter(|key| !map.contains_key(*key)).cloned().collect();
        (!absent.is_empty()).then(|| format!("{lang}: missing {}", absent.join(", ")))
    }).collect();
    Ok(CheckResult { ok: missing.is_empty(), keys: all.len(), message: if missing.is_empty() { "All language files have matching top-level keys".into() } else { missing.join(" · ") } })
}

#[cfg(target_os = "macos")]
fn build_menu<R: tauri::Runtime>(handle: &tauri::AppHandle<R>) -> tauri::Result<tauri::menu::Menu<R>> {
    use tauri::menu::{Menu, MenuItem, PredefinedMenuItem, Submenu};

    let menu = Menu::new(handle)?;

    // Notice: On macOS, the first Submenu's title (Self-Info Editor) will be replaced by the app's display name.
    // We still use "Self-Info Editor" as a fallback for Windows/Linux (although we only #[cfg]).
    let app = Submenu::new(handle, "Self-Info Editor", true)?;
    app.append(&PredefinedMenuItem::about(handle, Some("About Self-Info Editor"), None)?)?;
    app.append(&PredefinedMenuItem::separator(handle)?)?;
    app.append(&MenuItem::with_id(handle, "new-json", "New JSON", true, Some("CmdOrCtrl+N"))?)?;
    app.append(&MenuItem::with_id(handle, "new-md", "New Markdown", true, Some("CmdOrCtrl+Shift+N"))?)?;
    app.append(&PredefinedMenuItem::separator(handle)?)?;
    app.append(&MenuItem::with_id(handle, "open", "Open…", true, Some("CmdOrCtrl+O"))?)?;
    app.append(&PredefinedMenuItem::separator(handle)?)?;
    app.append(&MenuItem::with_id(handle, "save", "Save", true, Some("CmdOrCtrl+S"))?)?;
    app.append(&MenuItem::with_id(handle, "save-as", "Save As…", true, Some("CmdOrCtrl+Shift+S"))?)?;
    app.append(&PredefinedMenuItem::separator(handle)?)?;
    app.append(&PredefinedMenuItem::services(handle, Some("Services"))?)?;
    app.append(&PredefinedMenuItem::separator(handle)?)?;
    app.append(&PredefinedMenuItem::hide(handle, Some("Hide Self-Info Editor"))?)?;
    app.append(&PredefinedMenuItem::hide_others(handle, Some("Hide Others"))?)?;
    app.append(&PredefinedMenuItem::show_all(handle, Some("Show All"))?)?;
    app.append(&PredefinedMenuItem::separator(handle)?)?;
    app.append(&PredefinedMenuItem::quit(handle, Some("Quit Self-Info Editor"))?)?;
    menu.append(&app)?;

    let lang = Submenu::new(handle, "Language", true)?;
    lang.append(&MenuItem::with_id(handle, "lang-ja", "日本語", true, None::<&str>)?)?;
    lang.append(&MenuItem::with_id(handle, "lang-en", "Meow", true, None::<&str>)?)?;
    lang.append(&MenuItem::with_id(handle, "lang-zh-Hans", "华文", true, None::<&str>)?)?;
    lang.append(&MenuItem::with_id(handle, "lang-zh-TW", "繁體中文", true, None::<&str>)?)?;
    menu.append(&lang)?;

    // Category 3 / Tools (context actions)
    let tools = Submenu::new(handle, "Tools", true)?;
    tools.append(&MenuItem::with_id(handle, "format", "Format", true, Some("CmdOrCtrl+Shift+F"))?)?;
    tools.append(&MenuItem::with_id(handle, "minify", "Minify", true, Some("CmdOrCtrl+Shift+M"))?)?;
    tools.append(&MenuItem::with_id(handle, "validate", "Validate", true, Some("CmdOrCtrl+Shift+V"))?)?;
    tools.append(&PredefinedMenuItem::separator(handle)?)?;
    tools.append(&MenuItem::with_id(handle, "schema-check", "Schema Check", true, None::<&str>)?)?;
    tools.append(&MenuItem::with_id(handle, "wrap", "Wrap", true, None::<&str>)?)?;
    tools.append(&MenuItem::with_id(handle, "unwrap", "Unwrap", true, None::<&str>)?)?;
    tools.append(&MenuItem::with_id(handle, "normalize", "Normalize", true, None::<&str>)?)?;
    tools.append(&PredefinedMenuItem::separator(handle)?)?;
    tools.append(&MenuItem::with_id(handle, "add-entry", "Add Changelog Entry", true, None::<&str>)?)?;
    tools.append(&MenuItem::with_id(handle, "auto-number", "Auto-number Articles", true, None::<&str>)?)?;
    tools.append(&MenuItem::with_id(handle, "export-html", "Export HTML", true, None::<&str>)?)?;
    tools.append(&PredefinedMenuItem::separator(handle)?)?;
    tools.append(&MenuItem::with_id(handle, "check-i18n", "Check i18n Consistency", true, None::<&str>)?)?;
    menu.append(&tools)?;

    // Category 4 / View (toggle tree & preview)
    let view = Submenu::new(handle, "View", true)?;
    view.append(&MenuItem::with_id(handle, "toggle-tree", "Toggle Tree", true, Some("CmdOrCtrl+Shift+T"))?)?;
    view.append(&MenuItem::with_id(handle, "toggle-preview", "Toggle Preview", true, Some("CmdOrCtrl+Shift+P"))?)?;
    menu.append(&view)?;

    Ok(menu)
}

#[cfg(not(target_os = "macos"))]
fn build_menu<R: tauri::Runtime>(_handle: &tauri::AppHandle<R>) -> tauri::Result<Option<tauri::menu::Menu<R>>> {
    // Notice: On Windows / Linux, we don't use the Tauri's native menu bar.
    // The native Windows menu bar is not integrated with the window, and we use a custom macOS-style glass title menu bar.
    Ok(None)
}

pub fn run() {
    let builder = tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![read_text_file, write_text_file, list_files, check_i18n_consistency]);

    #[cfg(target_os = "macos")]
    let builder = builder
        .setup(|app| {
            let handle = app.handle().clone();
            let menu = build_menu(&handle)?;
            app.set_menu(menu)?;
            let for_event = handle.clone();
            app.on_menu_event(move |_app, event| {
                let id = event.id().0.clone();
                let _ = for_event.emit("menu:action", &id);
            });
            Ok(())
        });

    #[cfg(not(target_os = "macos"))]
    let builder = builder.setup(|app| {
        let handle = app.handle().clone();
        if let Some(menu) = build_menu(&handle)? {
            app.set_menu(menu)?;
            let for_event = handle.clone();
            app.on_menu_event(move |_app, event| {
                let id = event.id().0.clone();
                let _ = for_event.emit("menu:action", &id);
            });
        }
        Ok(())
    });

    builder
        .run(tauri::generate_context!())
        .expect("error while running Self-Info Editor");
}
