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

if [[ -z "$pptx_path" ]]; then
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
          <true/>
          <key>Types</key>
          <array>
            <string>com.apple.cocoa.string</string>
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
        <dict>
          <key>COMMAND_STRING</key>
          <dict/>
          <key>CheckedForUserDefaultShell</key>
          <dict/>
          <key>inputMethod</key>
          <dict/>
          <key>shell</key>
          <dict/>
          <key>source</key>
          <dict/>
        </dict>
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
          <string><![CDATA[set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:\$HOME/.local/bin:\$HOME/.cargo/bin:\$PATH"
ROOT_DIR="$ROOT_DIR"

run_pdf() {
  local PDF_PATH="\${1:-}"

  if [[ -z "\$PDF_PATH" ]]; then
    osascript -e 'display dialog "No PDF was provided to the Pro Data Analysis Quick Action." buttons {"OK"} default button 1 with icon caution'
    exit 1
  fi

  cd "\$ROOT_DIR"
  if ! OUTPUT="\$(uv run pro-data-analysis "\$PDF_PATH" 2>&1)"; then
    ERROR_MESSAGE="\$OUTPUT" osascript <<'APPLESCRIPT'
on run
  display dialog (system attribute "ERROR_MESSAGE") buttons {"OK"} default button 1 with icon caution
end run
APPLESCRIPT
    exit 1
  fi

  lines=("\${(@f)OUTPUT}")
  canonical_pdf="\${lines[1]}"
  ppt_ai="\${lines[4]}"
  workflow_json="\${lines[5]}"
  pptx_path="\${lines[7]:-}"

  if [[ -z "\$pptx_path" ]]; then
    osascript -e 'display notification "Working Illustrator file created. Finish the slide layout, save it, then run the Quick Action again." with title "Pro Data Analysis"'
    open -R "\$ppt_ai"
  else
    osascript -e 'display notification "Finished generating CMS files." with title "Pro Data Analysis"'
    open -R "\${pptx_path:-\$canonical_pdf}"
  fi
}

if (( \$# > 0 )); then
  for f in "\$@"; do
    run_pdf "\$f"
  done
else
  while IFS= read -r f; do
    [[ -n "\$f" ]] && run_pdf "\$f"
  done
fi]]></string>
          <key>CheckedForUserDefaultShell</key>
          <true/>
          <key>inputMethod</key>
          <integer>1</integer>
          <key>shell</key>
          <string>/bin/zsh</string>
          <key>source</key>
          <string></string>
        </dict>
        <key>BundleIdentifier</key>
        <string>com.apple.RunShellScript</string>
        <key>CFBundleVersion</key>
        <string>2.0.3</string>
        <key>CanShowSelectedItemsWhenRun</key>
        <false/>
        <key>CanShowWhenRun</key>
        <true/>
        <key>Category</key>
        <array>
          <string>AMCategoryUtilities</string>
        </array>
        <key>Class Name</key>
        <string>RunShellScriptAction</string>
        <key>InputUUID</key>
        <string>A5F716C0-9A0D-4D38-ADCC-8BAB97515274</string>
        <key>Keywords</key>
        <array>
          <string>Shell</string>
          <string>Script</string>
          <string>Command</string>
          <string>Run</string>
          <string>Unix</string>
        </array>
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
        <key>OutputUUID</key>
        <string>333E5DB7-2637-4DB7-BD4D-970E58E407BC</string>
        <key>UUID</key>
        <string>49F3EC34-C295-4DBE-9BD5-72EBC2A46063</string>
        <key>UnlocalizedApplications</key>
        <array>
          <string>Automator</string>
        </array>
        <key>arguments</key>
        <dict>
          <key>0</key>
          <dict>
            <key>default value</key>
            <integer>0</integer>
            <key>name</key>
            <string>inputMethod</string>
            <key>required</key>
            <string>0</string>
            <key>type</key>
            <string>0</string>
            <key>uuid</key>
            <string>0</string>
          </dict>
          <key>1</key>
          <dict>
            <key>default value</key>
            <false/>
            <key>name</key>
            <string>CheckedForUserDefaultShell</string>
            <key>required</key>
            <string>0</string>
            <key>type</key>
            <string>0</string>
            <key>uuid</key>
            <string>1</string>
          </dict>
          <key>2</key>
          <dict>
            <key>default value</key>
            <string></string>
            <key>name</key>
            <string>source</string>
            <key>required</key>
            <string>0</string>
            <key>type</key>
            <string>0</string>
            <key>uuid</key>
            <string>2</string>
          </dict>
          <key>3</key>
          <dict>
            <key>default value</key>
            <string></string>
            <key>name</key>
            <string>COMMAND_STRING</string>
            <key>required</key>
            <string>0</string>
            <key>type</key>
            <string>0</string>
            <key>uuid</key>
            <string>3</string>
          </dict>
          <key>4</key>
          <dict>
            <key>default value</key>
            <string>/bin/sh</string>
            <key>name</key>
            <string>shell</string>
            <key>required</key>
            <string>0</string>
            <key>type</key>
            <string>0</string>
            <key>uuid</key>
            <string>4</string>
          </dict>
        </dict>
        <key>conversionLabel</key>
        <integer>0</integer>
        <key>location</key>
        <string>309.000000:485.000000</string>
        <key>nibPath</key>
        <string>/System/Library/Automator/Run Shell Script.action/Contents/Resources/Base.lproj/main.nib</string>
      </dict>
      <key>isViewVisible</key>
      <true/>
    </dict>
  </array>
  <key>connectors</key>
  <dict/>
  <key>workflowMetaData</key>
  <dict>
    <key>applicationBundleID</key>
    <string>com.apple.finder</string>
    <key>applicationBundleIDsByDocumentType</key>
    <dict/>
    <key>applicationBundleIDsByPath</key>
    <dict>
      <key>/System/Library/CoreServices/Finder.app</key>
      <string>com.apple.finder</string>
    </dict>
    <key>applicationPath</key>
    <string>/System/Library/CoreServices/Finder.app</string>
    <key>applicationPaths</key>
    <array>
      <string>/System/Library/CoreServices/Finder.app</string>
    </array>
    <key>inputTypeIdentifier</key>
    <string>com.apple.Automator.fileSystemObject</string>
    <key>outputTypeIdentifier</key>
    <string>com.apple.Automator.nothing</string>
    <key>presentationMode</key>
    <integer>15</integer>
    <key>processesInput</key>
    <false/>
    <key>serviceApplicationBundleID</key>
    <string>com.apple.finder</string>
    <key>serviceApplicationPath</key>
    <string>/System/Library/CoreServices/Finder.app</string>
    <key>serviceInputTypeIdentifier</key>
    <string>com.apple.Automator.fileSystemObject</string>
    <key>serviceOutputTypeIdentifier</key>
    <string>com.apple.Automator.nothing</string>
    <key>serviceProcessesInput</key>
    <false/>
    <key>systemImageName</key>
    <string>NSActionTemplate</string>
    <key>useAutomaticInputType</key>
    <false/>
    <key>workflowTypeIdentifier</key>
    <string>com.apple.Automator.servicesMenu</string>
  </dict>
</dict>
</plist>
EOF

cat > "$CONTENTS_DIR/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>NSServices</key>
  <array>
    <dict>
      <key>NSBackgroundColorName</key>
      <string>background</string>
      <key>NSBackgroundSystemColorName</key>
      <string>blackColor</string>
      <key>NSIconName</key>
      <string>NSActionTemplate</string>
      <key>NSMenuItem</key>
      <dict>
        <key>default</key>
        <string>Pro Data Analysis</string>
      </dict>
      <key>NSMessage</key>
      <string>runWorkflowAsService</string>
      <key>NSRequiredContext</key>
      <dict>
        <key>NSApplicationIdentifier</key>
        <string>com.apple.finder</string>
      </dict>
      <key>NSSendFileTypes</key>
      <array>
        <string>com.adobe.pdf</string>
      </array>
    </dict>
  </array>
</dict>
</plist>
EOF

plutil -lint "$CONTENTS_DIR/document.wflow" "$CONTENTS_DIR/Info.plist" >/dev/null

if [[ -x /System/Library/CoreServices/pbs ]]; then
  /System/Library/CoreServices/pbs -flush >/dev/null 2>&1 || true
fi

echo "Installed Quick Action to $WORKFLOW_DIR"
echo "If Finder was already open, relaunch Finder or log out and back in if the menu does not update immediately."
