// Al Munadi -- Windows 11 Widget Board provider entry point.
// Hosted as a COM out-of-process server by the Widget Service. When the user
// adds/removes a widget the Service launches this process and routes
// IWidgetProvider callbacks to AlMunadiWidgetProvider. We block on a manual
// reset event until Deactivate(...) is called for the last widget, then exit.

using System;
using System.Runtime.InteropServices;
using System.Threading;
using AlMunadi.Widget;

namespace AlMunadi.Widget;

public static class Program
{
    private static readonly ManualResetEventSlim _exitEvent = new(false);
    private static int _activeWidgetCount;
    private const string WidgetServerArg = "-RegisterProcessAsComServer";

    [STAThread]
    public static int Main(string[] args)
    {
        var isComServer = false;
        foreach (var arg in args)
        {
            if (string.Equals(arg, WidgetServerArg, StringComparison.OrdinalIgnoreCase))
            {
                isComServer = true;
                break;
            }
        }

        if (!isComServer)
        {
            // Launched outside of the Widget Service (e.g. by the installer for
            // first-run registration). Nothing to do here -- exit silently.
            return 0;
        }

        // Register the COM class factory so the Widget Service can instantiate
        // AlMunadiWidgetProvider on demand.
        using var registration = ComRegistration.Register<AlMunadiWidgetProvider>();

        _exitEvent.Wait();
        return 0;
    }

    /// <summary>Bumped by <see cref="AlMunadiWidgetProvider.Activate"/>.</summary>
    public static void IncrementActiveWidgetCount() => Interlocked.Increment(ref _activeWidgetCount);

    /// <summary>Decremented by <see cref="AlMunadiWidgetProvider.Deactivate"/>; once zero, the host exits.</summary>
    public static void DecrementActiveWidgetCount()
    {
        if (Interlocked.Decrement(ref _activeWidgetCount) <= 0)
        {
            _exitEvent.Set();
        }
    }
}

internal sealed class ComRegistration : IDisposable
{
    private readonly uint _cookie;

    private ComRegistration(uint cookie) { _cookie = cookie; }

    public static ComRegistration Register<T>() where T : new()
    {
        var clsid = typeof(T).GUID;
        var hr = CoRegisterClassObject(
            ref clsid,
            new ComClassFactory<T>(),
            CLSCTX_LOCAL_SERVER,
            REGCLS_MULTIPLEUSE,
            out var cookie);
        if (hr != 0) Marshal.ThrowExceptionForHR(hr);
        return new ComRegistration(cookie);
    }

    public void Dispose()
    {
        if (_cookie != 0) CoRevokeClassObject(_cookie);
    }

    private const int CLSCTX_LOCAL_SERVER = 0x4;
    private const int REGCLS_MULTIPLEUSE = 1;

    [DllImport("ole32.dll")]
    private static extern int CoRegisterClassObject(
        ref Guid rclsid,
        [MarshalAs(UnmanagedType.IUnknown)] object pUnk,
        int dwClsContext,
        int flags,
        out uint lpdwRegister);

    [DllImport("ole32.dll")]
    private static extern int CoRevokeClassObject(uint dwRegister);
}

[ComVisible(true)]
[Guid("00000001-0000-0000-C000-000000000046")] // IClassFactory
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface IClassFactory
{
    [PreserveSig] int CreateInstance(IntPtr pUnkOuter, ref Guid riid, out IntPtr ppvObject);
    [PreserveSig] int LockServer(bool fLock);
}

[ComVisible(true)]
[ClassInterface(ClassInterfaceType.None)]
internal sealed class ComClassFactory<T> : IClassFactory where T : new()
{
    public int CreateInstance(IntPtr pUnkOuter, ref Guid riid, out IntPtr ppvObject)
    {
        ppvObject = IntPtr.Zero;
        if (pUnkOuter != IntPtr.Zero) return unchecked((int)0x80040110); // CLASS_E_NOAGGREGATION
        var instance = new T();
        var unk = Marshal.GetIUnknownForObject(instance!);
        try
        {
            return Marshal.QueryInterface(unk, ref riid, out ppvObject);
        }
        finally
        {
            Marshal.Release(unk);
        }
    }

    public int LockServer(bool fLock) => 0;
}
