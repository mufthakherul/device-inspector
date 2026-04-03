/// Inspecta Rust Plugin SDK skeleton.
#[derive(Debug, Clone)]
pub struct PluginResult {
    pub status: String,
    pub warnings: Vec<String>,
}

pub fn run(surface: &str) -> PluginResult {
    PluginResult {
        status: format!("ok:{surface}"),
        warnings: vec![],
    }
}
