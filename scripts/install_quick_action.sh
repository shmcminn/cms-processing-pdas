#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNNER="$ROOT_DIR/scripts/run_quick_action.sh"
SERVICE_DIR="$HOME/Library/Services"
WORKFLOW_DIR="$SERVICE_DIR/Pro Data Analysis.workflow"
CONTENTS_DIR="$WORKFLOW_DIR/Contents"

mkdir -p "$CONTENTS_DIR"

cat > "$RUNNER" <<'EOF'
#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PDF_PATH="${1:-}"

if [[ -z "$PDF_PATH" ]]; then
  osascript -e 'display dialog "No PDF was provided to the Pro Data Analysis Quick Action." buttons {"OK"} default button 1 with icon caution'
  exit 1
fi

cd "$ROOT_DIR"
if ! OUTPUT="$(uv run pro-data-analysis "$PDF_PATH" 2>&1)"; then
  ERROR_MESSAGE="$OUTPUT" osascript <<'APPLESCRIPT'
on run
  display dialog (system attribute "ERROR_MESSAGE") buttons {"OK"} default button 1 with icon caution
end run
APPLESCRIPT
  exit 1
fi

lines=("${(@f)OUTPUT}")
canonical_pdf="${lines[1]}"
main_jpg="${lines[2]}"
email_jpg="${lines[3]}"
ppt_ai="${lines[4]}"
workflow_json="${lines[5]}"
ppt_pdf="${lines[6]:-}"
pptx_path="${lines[7]:-}"

phase="$(sed -n 's/.*"phase": "\\([^"]*\\)".*/\\1/p' "$workflow_json" | head -n 1)"

if [[ "$phase" == "awaiting_manual_layout" ]]; then
  osascript -e 'display notification "Working Illustrator file created. Finish the slide layout, save it, then run the Quick Action again." with title "Pro Data Analysis"'
  open -R "$ppt_ai"
else
  osascript -e 'display notification "Finished generating CMS files." with title "Pro Data Analysis"'
  open -R "${pptx_path:-$canonical_pdf}"
fi
EOF

chmod +x "$RUNNER"

cat > "$CONTENTS_DIR/document.wflow" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>AMApplicationBuild</key>
  <string>554</string>
  <key>AMApplicationVersion</key>
  <string>2.10</string>
  <key>AMDocumentVersion</key>
  <string>2</string>
  <key>actions</key>
  <array>
    <dict>
      <key>action</key>
      <dict>
        <key>AMAccepts</key>
        <dict>
          <key>Container</key>
          <string>List</string>
          <key>Optional</key>
          <false/>
          <key>Types</key>
          <array>
            <string>com.adobe.pdf</string>
          </array>
        </dict>
        <key>AMActionVersion</key>
        <string>2.0.3</string>
        <key>AMApplication</key>
        <array>
          <string>Automator</string>
          <string>com.apple.Automator</string>
        </array>
        <key>AMParameterProperties</key>
        <dict/>
        <key>AMProvides</key>
        <dict>
          <key>Container</key>
          <string>List</string>
          <key>Types</key>
          <array>
            <string>com.apple.cocoa.string</string>
          </array>
        </dict>
        <key>ActionBundlePath</key>
        <string>/System/Library/Automator/Run Shell Script.action</string>
        <key>ActionName</key>
        <string>Run Shell Script</string>
        <key>ActionParameters</key>
        <dict>
          <key>COMMAND_STRING</key>
          <string>"$RUNNER" "\$1"</string>
          <key>CheckedForUserDefaultShell</key>
          <true/>
          <key>inputMethod</key>
          <integer>1</integer>
          <key>shell</key>
          <string>/bin/zsh</string>
          <key>source</key>
          <string>for f in "\$@"
do
  "$RUNNER" "\$f"
done</string>
        </dict>
        <key>BundleIdentifier</key>
        <string>com.apple.RunShellScript</string>
        <key>Category</key>
        <array>
          <string>AMCategoryUtilities</string>
        </array>
        <key>Class Name</key>
        <string>RunShellScriptAction</string>
        <key>Keywords</key>
        <array/>
        <key>NSServices</key>
        <array>
          <dict>
            <key>NSKeyEquivalent</key>
            <string></string>
            <key>NSMenuItem</key>
            <dict>
              <key>default</key>
              <string>Pro Data Analysis</string>
            </dict>
            <key>NSMessage</key>
            <string>runWorkflowAsService</string>
            <key>NSPortName</key>
            <string>Automator Runner</string>
            <key>NSSendFileTypes</key>
            <array>
              <string>com.adobe.pdf</string>
            </array>
          </dict>
        </array>
      </dict>
      <key>isViewVisible</key>
      <true/>
    </dict>
  </array>
  <key>connectors</key>
  <array/>
  <key>workflowMetaData</key>
  <dict>
    <key>applicationBundleID</key>
    <string>com.apple.finder</string>
    <key>applicationBundleIDsByDocumentType</key>
    <dict/>
    <key>serviceInputTypeIdentifier</key>
    <string>com.adobe.pdf</string>
    <key>serviceOutputTypeIdentifier</key>
    <string>com.apple.cocoa.string</string>
    <key>workflowTypeIdentifier</key>
    <string>com.apple.Automator.servicesMenu</string>
  </dict>
</dict>
</plist>
EOF

echo "Installed Quick Action to $WORKFLOW_DIR"
