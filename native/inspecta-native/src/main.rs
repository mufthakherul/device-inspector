use serde::Serialize;
use std::process;

/// Lightweight native helper for inspecta.
/// Emits a structured handshake payload so the Python agent can
/// discover native capabilities without hard dependencies.
#[derive(Serialize)]
struct Handshake {
    tool: &'static str,
    version: &'static str,
    language: &'static str,
    status: &'static str,
    os: &'static str,
    arch: &'static str,
    capabilities: Vec<Capability>,
}

#[derive(Serialize)]
struct Capability {
    name: &'static str,
    status: &'static str,
    detail: &'static str,
}

fn handshake() -> Handshake {
    Handshake {
        tool: "inspecta-native",
        version: env!("CARGO_PKG_VERSION"),
        language: "rust",
        status: "ok",
        os: std::env::consts::OS,
        arch: std::env::consts::ARCH,
        capabilities: vec![
            Capability {
                name: "disk_probe",
                status: "planned",
                detail: "intended for fio-backed quick disk probes",
            },
            Capability {
                name: "cpu_probe",
                status: "planned",
                detail: "intended for short CPU/memory microbenchmarks",
            },
            Capability {
                name: "ffi_bridge",
                status: "planned",
                detail: "to be exposed to Python via bindings/CLI wrapper",
            },
        ],
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.iter().any(|arg| arg == "--handshake") {
        let payload = handshake();
        match serde_json::to_string_pretty(&payload) {
            Ok(json) => {
                println!("{json}");
                return;
            }
            Err(err) => {
                eprintln!("inspecta-native: failed to serialize handshake: {err}");
                process::exit(2);
            }
        }
    }

    eprintln!("inspecta-native: use --handshake to print capabilities");
    process::exit(1);
}
