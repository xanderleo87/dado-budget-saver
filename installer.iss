; Inno Setup Script for Dado - Your Budget Saver
; Download Inno Setup from: https://jrsoftware.org/isinfo.php
; Open this file in Inno Setup Compiler and click Build > Compile

[Setup]
AppName=Dado - Your Budget Saver
AppVersion=1.0.0
AppPublisher=Dado
AppPublisherURL=https://github.com/dado-budget-saver
DefaultDirName={autopf}\Dado
DefaultGroupName=Dado
UninstallDisplayIcon={app}\Dado.exe
OutputDir=installer_output
OutputBaseFilename=DadoSetup_v1.0.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
SetupIconFile=
LicenseFile=
DisableProgramGroupPage=yes
DisableWelcomePage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checked
Name: "startupicon"; Description: "Launch Dado on Windows startup"; GroupDescription: "Additional options:"; Flags: unchecked

[Files]
; Include the entire build output folder
Source: "dist\Dado\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu shortcut
Name: "{group}\Dado"; Filename: "{app}\Dado.exe"
Name: "{group}\Uninstall Dado"; Filename: "{uninstallexe}"
; Desktop shortcut
Name: "{commondesktop}\Dado"; Filename: "{app}\Dado.exe"; Tasks: desktopicon

[Registry]
; Optional: Launch on startup
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "Dado"; ValueData: """{app}\Dado.exe"""; Flags: uninsdeletevalue; Tasks: startupicon

[Run]
; Launch after install
Filename: "{app}\Dado.exe"; Description: "Launch Dado"; Flags: nowait postinstall skipifsilent
