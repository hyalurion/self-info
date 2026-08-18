use std::{fs, path::{Path, PathBuf}};

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

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![read_text_file, write_text_file, list_files, check_i18n_consistency])
        .run(tauri::generate_context!())
        .expect("error while running Self-Info Editor");
}
