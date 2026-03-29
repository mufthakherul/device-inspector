class Inspecta < Formula
  desc "Local-first device diagnostics CLI with evidence bundle verification"
  homepage "https://github.com/mufthakherul/device-inspector"
  version "0.1.0"
  license "CannotRepresent"

  on_macos do
    url "https://github.com/mufthakherul/device-inspector/releases/download/v0.1.0/inspecta-0.1.0-macos.zip"
    sha256 "REPLACE_WITH_SHA256"
  end

  on_linux do
    url "https://github.com/mufthakherul/device-inspector/releases/download/v0.1.0/inspecta-0.1.0-linux.zip"
    sha256 "REPLACE_WITH_SHA256"
  end

  def install
    bin.install "inspecta"
  end

  test do
    system "#{bin}/inspecta", "--version"
  end
end
