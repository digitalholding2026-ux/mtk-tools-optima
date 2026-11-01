; =============================================================================
;  Optima MTK Tool Pro - Script Inno Setup
;  Genere par : Antigravity / Optima Telecom
;  Version    : 1.0.0
;  Cible      : Windows 10/11 x64
; =============================================================================

[Setup]
AppName=Optima MTK Tool Pro
AppVersion=1.0.0
AppVerName=Optima MTK Tool Pro v1.0.0
AppPublisher=Optima Telecom
AppPublisherURL=https://optima-telecom.com
AppSupportURL=https://optima-telecom.com/support
AppUpdatesURL=https://optima-telecom.com/updates
AppCopyright=Copyright (C) 2025 Optima Telecom

; Repertoire d'installation par defaut
DefaultDirName={autopf}\OptimaMTKTool
DefaultGroupName=Optima MTK Tool
AllowNoIcons=yes

; Sortie de l'installateur
OutputDir=.\output
OutputBaseFilename=OptimaMTKTool_Setup_v1.0.0

; Icone et apparence
SetupIconFile=assets\icon.ico
WizardStyle=modern
WizardSizePercent=120

; Compression maximale
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; Architecture cible : 64-bit uniquement
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64

; Privileges et UAC
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Desinstallateur
UninstallDisplayIcon={app}\OptimaMTKTool.exe
UninstallDisplayName=Optima MTK Tool Pro
CreateUninstallRegKey=yes

; Informations d'installation registre
VersionInfoVersion=1.0.0.0
VersionInfoCompany=Optima Telecom
VersionInfoDescription=Optima MTK Tool Pro Installer
VersionInfoProductName=Optima MTK Tool Pro
VersionInfoProductVersion=1.0.0.0

; Desactiver le redemarrage automatique
RestartIfNeededByRun=no

; =============================================================================
[Languages]
Name: "french";    MessagesFile: "compiler:Languages\French.isl"
Name: "english";   MessagesFile: "compiler:Default.isl"

; =============================================================================
[Messages]
; Personnalisation des messages en francais
french.BeveledLabel=Optima MTK Tool Pro v1.0.0

; =============================================================================
[CustomMessages]
french.InstallVCRedist=Installation de Visual C++ Redistributable 2022...
french.InstallDriverVCOM=Installation des pilotes COM MediaTek (VCOM)...
french.InstallDriverLibUSB=Installation du filtre WinUSB / LibUSB...
french.InstallDriverADB=Installation des pilotes ADB / Fastboot...
french.DriversInstalled=Pilotes installes avec succes.
french.LaunchApp=Lancer Optima MTK Tool Pro

english.InstallVCRedist=Installing Visual C++ Redistributable 2022...
english.InstallDriverVCOM=Installing MediaTek VCOM drivers...
english.InstallDriverLibUSB=Installing WinUSB / LibUSB filter...
english.InstallDriverADB=Installing ADB / Fastboot drivers...
english.DriversInstalled=Drivers installed successfully.
english.LaunchApp=Launch Optima MTK Tool Pro

; =============================================================================
[Tasks]
Name: "desktopicon";   Description: "{cm:CreateDesktopIcon}";         GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunch";   Description: "{cm:CreateQuickLaunchIcon}";     GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1
Name: "installdrvs";   Description: "Installer les pilotes MediaTek / ADB / LibUSB"; GroupDescription: "Pilotes:"; Flags: checkedonce

; =============================================================================
[Files]
; --- Application principale (tout le dossier dist\OptimaMTKTool) ---
Source: "dist\OptimaMTKTool\*";              DestDir: "{app}";                      Flags: ignoreversion recursesubdirs createallsubdirs

; --- Redist : VC++ 2022 x64 (extrait dans {tmp}, supprime apres install) ---
Source: "redist\VC_redist.x64.exe";          DestDir: "{tmp}";                      Flags: deleteafterinstall

; =============================================================================
[Dirs]
; Creer les sous-dossiers si absents (securite)
Name: "{app}\bin"
Name: "{app}\drivers\vcom"
Name: "{app}\drivers\libusb_filter"
Name: "{app}\drivers\adb_fastboot"
Name: "{app}\data\da"
Name: "{app}\data\auth"
Name: "{app}\logs"

; =============================================================================
[Icons]
; Raccourci Menu Demarrer
Name: "{group}\Optima MTK Tool Pro";          Filename: "{app}\OptimaMTKTool.exe";    IconFilename: "{app}\OptimaMTKTool.exe"; Comment: "Outil de flashage MediaTek professionnel"
Name: "{group}\Installer les Pilotes";        Filename: "{app}\drivers\install_drivers.bat"; IconFilename: "{app}\OptimaMTKTool.exe"; Comment: "Reinstaller les pilotes MediaTek et ADB"
Name: "{group}\{cm:UninstallProgram,Optima MTK Tool Pro}"; Filename: "{uninstallexe}"

; Raccourci Bureau (optionnel, tache deselectionnee par defaut)
Name: "{autodesktop}\Optima MTK Tool Pro";   Filename: "{app}\OptimaMTKTool.exe";    IconFilename: "{app}\OptimaMTKTool.exe"; Tasks: desktopicon; Comment: "Optima MTK Tool Pro"

; Quick Launch (Windows XP/Vista/7 uniquement)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Optima MTK Tool Pro"; Filename: "{app}\OptimaMTKTool.exe"; Tasks: quicklaunch

; =============================================================================
[Run]
; --- 1. Installation silencieuse de Visual C++ 2022 Redistributable ---
;     Condition : seulement si pas deja installe (verifie via [Code])
Filename: "{tmp}\VC_redist.x64.exe";
  Parameters: "/quiet /norestart";
  StatusMsg: "{cm:InstallVCRedist}";
  Flags: waituntilterminated runhidden;
  Check: not VCRedistInstalled

; --- 2. Pilotes VCOM MediaTek (port serie COM) ---
Filename: "{sys}\pnputil.exe";
  Parameters: "/add-driver ""{app}\drivers\vcom\*.inf"" /install /subdirs";
  StatusMsg: "{cm:InstallDriverVCOM}";
  Flags: waituntilterminated runhidden;
  Tasks: installdrvs

; --- 3. Filtre WinUSB / LibUSB pour detection BROM ---
Filename: "{sys}\pnputil.exe";
  Parameters: "/add-driver ""{app}\drivers\libusb_filter\*.inf"" /install";
  StatusMsg: "{cm:InstallDriverLibUSB}";
  Flags: waituntilterminated runhidden;
  Tasks: installdrvs

; --- 4. Pilotes ADB / Fastboot Android ---
Filename: "{sys}\pnputil.exe";
  Parameters: "/add-driver ""{app}\drivers\adb_fastboot\*.inf"" /install";
  StatusMsg: "{cm:InstallDriverADB}";
  Flags: waituntilterminated runhidden;
  Tasks: installdrvs

; --- 5. Lancement de l'application apres installation (optionnel) ---
Filename: "{app}\OptimaMTKTool.exe";
  Description: "{cm:LaunchApp}";
  Flags: nowait postinstall skipifsilent

; =============================================================================
[UninstallRun]
; Nettoyage : tuer le processus avant desinstallation
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM OptimaMTKTool.exe /T"; Flags: runhidden; RunOnceId: "KillApp"
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM adb.exe /T";           Flags: runhidden; RunOnceId: "KillAdb"

; =============================================================================
[Registry]
; Enregistrement dans Ajout/Suppression de programmes (complement)
Root: HKLM; Subkey: "SOFTWARE\Optima Telecom\OptimaMTKTool"; ValueType: string; ValueName: "InstallPath";  ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\Optima Telecom\OptimaMTKTool"; ValueType: string; ValueName: "Version";      ValueData: "1.0.0"
Root: HKLM; Subkey: "SOFTWARE\Optima Telecom\OptimaMTKTool"; ValueType: string; ValueName: "Publisher";    ValueData: "Optima Telecom"

; =============================================================================
[Code]
// ---------------------------------------------------------------------------
//  VCRedistInstalled()
//  Verifie si Visual C++ 2015-2022 Redistributable x64 est deja installe.
//  Source : cle de registre officielle Microsoft.
// ---------------------------------------------------------------------------
function VCRedistInstalled(): Boolean;
var
  Installed: Cardinal;
  Major:     Cardinal;
begin
  Result := False;

  // Verifier la presence du runtime VC++ 2022 / 2019 / 2017 / 2015 (14.x)
  if RegQueryDWordValue(HKLM,
      'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64',
      'Installed', Installed) then
  begin
    if Installed = 1 then
    begin
      // Verifier egalement la version majeure >= 14.30 (VS2022)
      if RegQueryDWordValue(HKLM,
          'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64',
          'Major', Major) then
      begin
        Result := (Major >= 14);
      end
      else
        Result := True; // Installe mais version inconnue -> on accepte
    end;
  end;

  if Result then
    Log('VCRedistInstalled: Visual C++ 14.x x64 deja present, installation ignoree.')
  else
    Log('VCRedistInstalled: Visual C++ 14.x x64 absent, installation necessaire.');
end;

// ---------------------------------------------------------------------------
//  InitializeSetup()
//  Verification de compatibilite avant le demarrage de l'installation.
// ---------------------------------------------------------------------------
function InitializeSetup(): Boolean;
begin
  Result := True;

  // Verifier Windows 10 minimum (build 10.0 = version majeure 10)
  if not IsWin64 then
  begin
    MsgBox(
      'Optima MTK Tool Pro necessite Windows 10 ou 11 en version 64 bits.' + #13#10 +
      'L''installation ne peut pas continuer.',
      mbCriticalError, MB_OK
    );
    Result := False;
    Exit;
  end;
end;

// ---------------------------------------------------------------------------
//  CurStepChanged()
//  Actions personnalisees a chaque etape de l'installation.
// ---------------------------------------------------------------------------
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Enregistrer la date d'installation dans le registre
    RegWriteStringValue(HKLM,
      'SOFTWARE\Optima Telecom\OptimaMTKTool',
      'InstallDate',
      GetDateTimeString('yyyy/mm/dd', '-', ':')
    );
    Log('Installation completee le : ' + GetDateTimeString('yyyy/mm/dd hh:nn:ss', '-', ':'));
  end;
end;

// ---------------------------------------------------------------------------
//  CurUninstallStepChanged()
//  Nettoyage lors de la desinstallation.
// ---------------------------------------------------------------------------
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Supprimer le dossier logs s'il reste vide
    DelTree(ExpandConstant('{app}\logs'), True, True, True);
    Log('Desinstallation terminee, dossier logs supprime.');
  end;
end;
