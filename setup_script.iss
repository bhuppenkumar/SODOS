[Setup]
AppName=SODOS
AppVersion=1.0.0
AppPublisher=Product Lab
DefaultDirName={autopf}\SODOS
DefaultGroupName=SODOS
OutputDir=dist_installer
OutputBaseFilename=SODOS_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\SODOS.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SODOS"; Filename: "{app}\SODOS.exe"
Name: "{autodesktop}\SODOS"; Filename: "{app}\SODOS.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SODOS.exe"; Description: "{cm:LaunchProgram,SODOS}"; Flags: nowait postinstall skipifsilent