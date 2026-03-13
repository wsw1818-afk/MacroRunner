; Inno Setup Script for MacroRunner
; MacroRunner 설치 프로그램

#define MyAppName "MacroRunner"
#define MyAppVersion "2.0"
#define MyAppPublisher "MacroRunner"
#define MyAppExeName "MacroRunner.exe"

[Setup]
; 앱 고유 ID
AppId={{A7B8C9D0-E1F2-3456-7890-ABCDEF123456}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; 출력 설정
OutputDir=installer_output
OutputBaseFilename=MacroRunner_Setup
; 압축 설정
Compression=lzma2
SolidCompression=yes
; 권한 설정
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; UI 설정
WizardStyle=modern
; 제거 설정
Uninstallable=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
; 제거 시 폴더 완전 삭제 확인
DirExistsWarning=no
CreateUninstallRegKey=yes

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; 메인 실행 파일
Source: "dist\MacroRunner\MacroRunner.exe"; DestDir: "{app}"; Flags: ignoreversion
; _internal 폴더 (PyInstaller 6.x 구조 - 모든 라이브러리 포함)
Source: "dist\MacroRunner\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
; macros 폴더
Source: "dist\MacroRunner\macros\*"; DestDir: "{app}\macros"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; backups 폴더 생성 (런타임에 사용)
Name: "{app}\backups"; Flags: uninsalwaysuninstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 제거 시 모든 파일과 폴더 완전 삭제
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}\macros"
Type: filesandordirs; Name: "{app}\backups"
Type: files; Name: "{app}\*.exe"
Type: files; Name: "{app}\*.dll"
Type: files; Name: "{app}\*.pyd"
Type: files; Name: "{app}\*.log"
Type: files; Name: "{app}\*.json"
Type: dirifempty; Name: "{app}"

[UninstallRun]
; 제거 전 실행 중인 앱 종료 (선택적)
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM MacroRunner.exe"; Flags: runhidden; RunOnceId: "KillApp"

[Code]
// 제거 시 확인 메시지
function InitializeUninstall(): Boolean;
begin
  Result := True;
  if MsgBox('MacroRunner를 완전히 제거하시겠습니까?'#13#13'설치 폴더의 모든 파일이 삭제됩니다.', mbConfirmation, MB_YESNO) = IDNO then
    Result := False;
end;

// 제거 완료 후 남은 폴더 정리
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AppDir: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    AppDir := ExpandConstant('{app}');
    // 남은 폴더 삭제 시도
    if DirExists(AppDir) then
    begin
      DelTree(AppDir, True, True, True);
    end;
  end;
end;
