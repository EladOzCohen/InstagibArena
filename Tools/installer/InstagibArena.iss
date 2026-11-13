; Instagib Arena - Windows installer (Inno Setup 6)
;
; Build it with:   ISCC.exe Tools\installer\InstagibArena.iss
; Needs the packaged game in Builds\Windows (see Tools\package_and_installer.ps1).
; The result is  Builds\InstagibArena_Setup_<version>.exe

#define AppName "Instagib Arena"
#define AppVersion "1.4.0"
#define AppExe "InstagibArena.exe"
#define BuildDir "..\..\Builds\Windows"

[Setup]
AppId={{1A524368-4344-4442-A62B-35B4D3C32CE1}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=EladOzCohen
AppCopyright=Copyright (C) 2026 EladOzCohen
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; One administrator prompt lets the installer add the Visual C++ runtime and the firewall rule.
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=commandline
OutputDir=..\..\Builds
OutputBaseFilename=InstagibArena_Setup_{#AppVersion}
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
InfoBeforeFile=InstallInfo.txt
ShowLanguageDialog=auto
SetupLogging=yes
ExtraDiskSpaceRequired=0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"

[CustomMessages]
english.TaskFirewall=Allow the game through Windows Firewall (needed to host or join games)
english.GroupNetwork=Network:
english.InstallingVCRedist=Installing the Microsoft Visual C++ runtime...
hebrew.TaskFirewall=אפשר למשחק לעבור בחומת האש של Windows (נדרש כדי לארח או להצטרף למשחק)
hebrew.GroupNetwork=רשת:
hebrew.InstallingVCRedist=מתקין את רכיבי Microsoft Visual C++...

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "firewall"; Description: "{cm:TaskFirewall}"; GroupDescription: "{cm:GroupNetwork}"; Check: IsAdminInstallMode

[Files]
; The whole packaged game, except the ARM redistributable that a PC with this game cannot use.
Source: "{#BuildDir}\*"; DestDir: "{app}"; Excludes: "vc_redist.arm64.exe"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
; Microsoft's runtime that every Unreal game needs. Skipped when it is already installed.
Filename: "{app}\Engine\Extras\Redist\en-us\vc_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "{cm:InstallingVCRedist}"; Check: VCRedistNeeded; Flags: waituntilterminated
; Lets friends connect to a game you host.
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall add rule name=""{#AppName}"" dir=in action=allow program=""{app}\InstagibArena\Binaries\Win64\InstagibArena-Win64-Shipping.exe"" enable=yes profile=any"; Tasks: firewall; Flags: runhidden
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""{#AppName}"""; RunOnceId: "RemoveFirewallRule"; Flags: runhidden

[UninstallDelete]
; Settings written by the game (volumes, logs).
Type: filesandordirs; Name: "{localappdata}\InstagibArena"

[Code]
function VCRedistNeeded: Boolean;
var
  Installed: Cardinal;
begin
  Result := True;
  if RegQueryDWordValue(HKLM64, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Installed', Installed) then
    Result := (Installed <> 1);
end;
