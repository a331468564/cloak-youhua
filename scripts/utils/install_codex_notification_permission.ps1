$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$notifyScript = Join-Path $projectRoot "scripts\notify_user.ps1"
$shortcutDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$shortcutPath = Join-Path $shortcutDir "Codex Project Notifier.lnk"
$appId = "Codex.Project.Notifier"

if (-not (Test-Path $notifyScript)) {
    throw "Missing notification script: $notifyScript"
}

New-Item -ItemType Directory -Path $shortcutDir -Force | Out-Null

$code = @"
using System;
using System.Text;
using System.Runtime.InteropServices;

[ComImport, Guid("0000010b-0000-0000-C000-000000000046"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IPersistFile
{
    void GetClassID(out Guid pClassID);
    int IsDirty();
    void Load([MarshalAs(UnmanagedType.LPWStr)] string pszFileName, uint dwMode);
    void Save([MarshalAs(UnmanagedType.LPWStr)] string pszFileName, bool fRemember);
    void SaveCompleted([MarshalAs(UnmanagedType.LPWStr)] string pszFileName);
    void GetCurFile([MarshalAs(UnmanagedType.LPWStr)] out string ppszFileName);
}

[ComImport, Guid("00021401-0000-0000-C000-000000000046"), ClassInterface(ClassInterfaceType.None)]
public class CShellLink {}

[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
public struct WIN32_FIND_DATAW
{
    public uint dwFileAttributes;
    public System.Runtime.InteropServices.ComTypes.FILETIME ftCreationTime;
    public System.Runtime.InteropServices.ComTypes.FILETIME ftLastAccessTime;
    public System.Runtime.InteropServices.ComTypes.FILETIME ftLastWriteTime;
    public uint nFileSizeHigh;
    public uint nFileSizeLow;
    public uint dwReserved0;
    public uint dwReserved1;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)]
    public string cFileName;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 14)]
    public string cAlternateFileName;
}

[ComImport, Guid("000214F9-0000-0000-C000-000000000046"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IShellLinkW
{
    void GetPath([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszFile, int cchMaxPath, IntPtr pfd, uint fFlags);
    void GetIDList(out IntPtr ppidl);
    void SetIDList(IntPtr pidl);
    void GetDescription([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszName, int cchMaxName);
    void SetDescription([MarshalAs(UnmanagedType.LPWStr)] string pszName);
    void GetWorkingDirectory([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszDir, int cchMaxPath);
    void SetWorkingDirectory([MarshalAs(UnmanagedType.LPWStr)] string pszDir);
    void GetArguments([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszArgs, int cchMaxPath);
    void SetArguments([MarshalAs(UnmanagedType.LPWStr)] string pszArgs);
    void GetHotkey(out short pwHotkey);
    void SetHotkey(short wHotkey);
    void GetShowCmd(out int piShowCmd);
    void SetShowCmd(int iShowCmd);
    void GetIconLocation([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszIconPath, int cchIconPath, out int piIcon);
    void SetIconLocation([MarshalAs(UnmanagedType.LPWStr)] string pszIconPath, int iIcon);
    void SetRelativePath([MarshalAs(UnmanagedType.LPWStr)] string pszPathRel, uint dwReserved);
    void Resolve(IntPtr hwnd, uint fFlags);
    void SetPath([MarshalAs(UnmanagedType.LPWStr)] string pszFile);
}

[ComImport, Guid("00000138-0000-0000-C000-000000000046"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IPropertyStore
{
    void GetCount(out uint cProps);
    void GetAt(uint iProp, out PROPERTYKEY pkey);
    void GetValue(ref PROPERTYKEY key, out PROPVARIANT pv);
    void SetValue(ref PROPERTYKEY key, ref PROPVARIANT pv);
    void Commit();
}

[StructLayout(LayoutKind.Sequential, Pack = 4)]
public struct PROPERTYKEY
{
    public Guid fmtid;
    public uint pid;
}

[StructLayout(LayoutKind.Sequential)]
public struct PROPVARIANT
{
    public ushort vt;
    public ushort wReserved1;
    public ushort wReserved2;
    public ushort wReserved3;
    public IntPtr p;
    public int p2;
}

public static class ShortcutAppId
{
    enum GETPROPERTYSTOREFLAGS : uint
    {
        GPS_DEFAULT = 0x00000000,
        GPS_READWRITE = 0x00000002
    }

    [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
    static extern int SHGetPropertyStoreFromParsingName(
        [MarshalAs(UnmanagedType.LPWStr)] string pszPath,
        IntPtr pbc,
        GETPROPERTYSTOREFLAGS flags,
        ref Guid riid,
        out IntPtr propertyStore
    );

    public static void CreateShortcut(string shortcutPath, string targetPath, string arguments, string workingDirectory, string iconPath, string description)
    {
        var shellLink = (IShellLinkW)new CShellLink();
        shellLink.SetPath(targetPath);
        shellLink.SetArguments(arguments);
        shellLink.SetWorkingDirectory(workingDirectory);
        shellLink.SetIconLocation(iconPath, 0);
        shellLink.SetDescription(description);
        ((IPersistFile)shellLink).Save(shortcutPath, true);
    }

    public static void Set(string shortcutPath, string appId)
    {
        object shellLinkObject;
        IShellLinkW shellLink;
        IPersistFile persistFile;

        try
        {
            shellLinkObject = new CShellLink();
            shellLink = GetComInterface<IShellLinkW>(
                shellLinkObject,
                new Guid("000214F9-0000-0000-C000-000000000046"),
                "IShellLinkW"
            );
        }
        catch (Exception ex)
        {
            throw new InvalidOperationException("Failed to create IShellLinkW from ShellLink CLSID.", ex);
        }

        try
        {
            persistFile = GetComInterface<IPersistFile>(
                shellLinkObject,
                new Guid("0000010b-0000-0000-C000-000000000046"),
                "IPersistFile"
            );
            persistFile.Load(shortcutPath, 0);
        }
        catch (Exception ex)
        {
            throw new InvalidOperationException("Failed to load shortcut through IPersistFile.", ex);
        }

        IPropertyStore propertyStore;
        try
        {
            propertyStore = GetComInterface<IPropertyStore>(
                shellLinkObject,
                new Guid("00000138-0000-0000-C000-000000000046"),
                "IPropertyStore"
            );
        }
        catch (Exception)
        {
            try
            {
                propertyStore = GetShortcutPropertyStore(shortcutPath);
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException("Failed to open shortcut property store through both ShellLink and SHGetPropertyStoreFromParsingName.", ex);
            }
        }

        try
        {
            SetAppIdProperty(propertyStore, appId);
            persistFile.Save(shortcutPath, true);
        }
        catch (Exception ex)
        {
            throw new InvalidOperationException("Failed to write AppUserModelID to shortcut property store.", ex);
        }
    }

    static T GetComInterface<T>(object comObject, Guid iid, string interfaceName)
    {
        IntPtr unknown = IntPtr.Zero;
        IntPtr typed = IntPtr.Zero;

        try
        {
            unknown = Marshal.GetIUnknownForObject(comObject);
            int hr = Marshal.QueryInterface(unknown, ref iid, out typed);
            if (hr != 0)
            {
                Marshal.ThrowExceptionForHR(hr);
            }

            return (T)Marshal.GetObjectForIUnknown(typed);
        }
        catch (Exception ex)
        {
            throw new InvalidOperationException("Failed to acquire COM interface " + interfaceName + ".", ex);
        }
        finally
        {
            if (typed != IntPtr.Zero)
            {
                Marshal.Release(typed);
            }

            if (unknown != IntPtr.Zero)
            {
                Marshal.Release(unknown);
            }
        }
    }

    static IPropertyStore GetShortcutPropertyStore(string shortcutPath)
    {
        var iid = new Guid("00000138-0000-0000-C000-000000000046");
        IntPtr propertyStorePtr;
        int hr = SHGetPropertyStoreFromParsingName(
            shortcutPath,
            IntPtr.Zero,
            GETPROPERTYSTOREFLAGS.GPS_READWRITE,
            ref iid,
            out propertyStorePtr
        );

        if (hr != 0)
        {
            Marshal.ThrowExceptionForHR(hr);
        }

        try
        {
            return (IPropertyStore)Marshal.GetObjectForIUnknown(propertyStorePtr);
        }
        finally
        {
            if (propertyStorePtr != IntPtr.Zero)
            {
                Marshal.Release(propertyStorePtr);
            }
        }
    }

    static void SetAppIdProperty(IPropertyStore propertyStore, string appId)
    {
        var appUserModelId = new PROPERTYKEY {
            fmtid = new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3"),
            pid = 5
        };

        var pv = new PROPVARIANT();
        pv.vt = 31; // VT_LPWSTR
        pv.p = Marshal.StringToCoTaskMemUni(appId);
        try
        {
            propertyStore.SetValue(ref appUserModelId, ref pv);
            propertyStore.Commit();
        }
        finally
        {
            if (pv.p != IntPtr.Zero)
            {
                Marshal.FreeCoTaskMem(pv.p);
            }
        }
    }
}
"@

Add-Type -TypeDefinition $code
$targetPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$notifyScript`""
[ShortcutAppId]::CreateShortcut(
    $shortcutPath,
    $targetPath,
    $arguments,
    $projectRoot,
    $targetPath,
    "Codex project notification helper"
)

$appIdAssigned = $false
try {
    [ShortcutAppId]::Set($shortcutPath, $appId)
    $appIdAssigned = $true
}
catch {
    Write-Warning "Could not assign AppUserModelID to shortcut through COM on this system."
    Write-Warning $_.Exception.Message
}

$notificationSettingsPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings\$appId"
New-Item -Path $notificationSettingsPath -Force | Out-Null
New-ItemProperty -Path $notificationSettingsPath -Name "Enabled" -Value 1 -PropertyType DWord -Force | Out-Null

Write-Host "Installed Codex notification shortcut:"
Write-Host $shortcutPath
Write-Host "AppUserModelID: $appId"
Write-Host "Shortcut AppUserModelID assigned: $appIdAssigned"
Write-Host ""
Write-Host "If notifications still do not appear, open Windows Settings > System > Notifications,"
Write-Host "then enable notifications for Codex Project Notifier or Windows PowerShell."
Write-Host ""
Write-Host "Testing notification now..."

powershell -NoProfile -ExecutionPolicy Bypass -File $notifyScript -Title "Codex permission test" -Message "Codex notification permission test"
