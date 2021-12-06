%global commit0     14b90ff9d9f031391a299e6e006965d02bfd1bb1
%global shortcommit0 %(c=%{commit0}; echo ${c:0:7})

%global     _vc_libdir  %{_libdir}/vc

Name:       raspberrypi-vc
Version:    2021206
Release:    1.20211206194915589553.master%{?dist}
Summary:    VideoCore GPU libraries, utilities and demos for Raspberry Pi
License:    BSD
URL:        https://github.com/raspberrypi
Source0:    userland-2021206.tar.gz
Source2:    10-vchiq.rules
# Patch0 fixes up paths for relocation from /opt to system directories.
# Needs rebase or dropped
#Patch0:     raspberrypi-vc-demo-source-path-fixup.patch

# Install libraries as per GNU Coding Standards
# Upstream reference: https://github.com/raspberrypi/userland/pull/650
#Patch0:     0001-Install-libraries-as-per-GNU-Coding-Standards.patch
#Patch1:     0001-Install-manual-pages-as-per-GNU-Coding-Standards.patch
ExclusiveArch:  armv7hl aarch64

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  systemd
BuildRequires:  coreutils

# Packages using raspberrypi-vc must Requires this:
#%%{?raspberrypi_vc_version:Requires: raspberrypi_vc%%{?_isa} = %%{raspberrypi_vc_version}}

%description
Libraries, utilities and demos for the Raspberry Pi BCM283x SOC GPUs


%package libs
Summary:    Libraries for accessing the Raspberry Pi GPU
# TO-DO: verify bcm283x-firmware pkg from Fedora is appropriate here
#Requires:   bcm283x-firmware

%description libs
Shared libraries for accessing the BCM283x VideoCore GPU on the RaspberryPi.


%package devel
Summary:    Headers for libraries that access the Raspberry Pi GPU
Requires:   %{name}-libs%{?_isa} = %{version}
License:    GPLv2+
Provides:   compat-%{name}-devel = %{version}-%{release}

%description devel
Header files for accessing the BCM283x VideoCore GPU on the Raspberry Pi.


%package demo-source
Summary:    Demo source for accessing the Raspberry Pi GPU
# Not to use %%{?_isa} on noarch package
Requires:   %{name}-libs = %{version}
License:    ASL 2.0
BuildArch:  noarch

%description demo-source
Demo source code for accessing the BCM283x VideoCore GP on the Raspberry Pi.


%package utils
Summary:    Utilities related to the Raspberry Pi GPU
Requires:   %{name}-libs%{?_isa} = %{version}

%description utils
Utilities for using the BCM283x VideoCore GPU on the Raspberry Pi.


%package static
Summary:    Static libraries for accessing the Raspberry Pi GPU
Requires:   %{name}-libs%{?_isa} = %{version}

%description static
Static versions of libraries for accessing the BCM283x VideoCore GPU on the
Raspberry Pi.


%prep
%autosetup -p1 -n userland-2021206


%build
# Must set BUILD_SHARED_LIBS=OFF and BUILD_STATIC_LIBS=ON
# See for details: https://github.com/raspberrypi/userland/pull/333
%cmake \
%ifarch aarch64
        -DARM64:BOOL=ON \
%endif
        -DCMAKE_BUILD_TYPE=Release \
        -DVMCS_INSTALL_PREFIX=%{_prefix} \
        -DBUILD_SHARED_LIBS:BOOL=OFF \
        -DBUILD_STATIC_LIBS:BOOL=ON \
        -DLIBDIR="%{_lib}/vc" \

%cmake_build


%install
%cmake_install

#RPM Macros support
mkdir -p %{buildroot}%{rpmmacrodir}
cat > %{buildroot}%{rpmmacrodir}/macros.%{name} << EOF
# raspberrypi-vc RPM Macros
%raspberrypi_vc_version	   %{version}
EOF
# Yes - the filename really is spelled LICENCE
touch -r LICENCE %{buildroot}%{rpmmacrodir}/macros.%{name}

### libs
%ifarch armv7hl
mv %{buildroot}/%{_libdir}/plugins %{buildroot}/%{_libdir}/vc
%endif

### pkgconfig
mv %{buildroot}/%{_libdir}/pkgconfig %{buildroot}/%{_libdir}/vc
mkdir -p %{buildroot}/%{_datadir}/pkgconfig
for i in %{buildroot}/%{_libdir}/vc/pkgconfig/*.pc; do
    sed -i "/^prefix=.*$/d" $i
    sed -i "/^exec_prefix=.*$/d" $i
    sed -i "s|^libdir=.*$|libdir=%{_libdir}/vc|" $i
    sed -i "s|^includedir=.*$|includedir=%{_includedir}/vc|" $i
    pkgpc=$(echo $i|sed 's|%{buildroot}/%{_libdir}/vc/pkgconfig/||')
    ln -s %{_libdir}/vc/pkgconfig/$pkgpc %{buildroot}/%{_datadir}/pkgconfig/$pkgpc
done

### devel
mkdir -p %{buildroot}/%{_includedir}/vc
shopt -s extglob
mv %{buildroot}/%{_includedir}/!(vc) %{buildroot}/%{_includedir}/vc
shopt -u extglob

### demo source
mkdir -p %{buildroot}/%{_usrsrc}/%{name}-demo-source
mv %{buildroot}/%{_usrsrc}/hello_pi %{buildroot}/%{_usrsrc}/%{name}-demo-source

### remove sysvinit vcfiled
rm -rf %{buildroot}%{_sysconfdir}/init.d
rm -rf %{buildroot}%{_prefix}%{_sysconfdir}/init.d
rm -rf %{buildroot}%{_datadir}/install

### install ldconfig conf
install -m 0755 -d    %{buildroot}%{_sysconfdir}/ld.so.conf.d/
echo "%{_vc_libdir}" >%{buildroot}%{_sysconfdir}/ld.so.conf.d/%{name}-%{_lib}.conf

### install udev rules
mkdir -p %{buildroot}%{_udevrulesdir}
install -D -p -m 0644 %{SOURCE2} %{buildroot}%{_udevrulesdir}/

### create compatibility links
mkdir -p %{buildroot}/opt/vc
ln -s %{_libdir}/vc %{buildroot}/opt/vc/lib
ln -s %{_includedir}/vc %{buildroot}/opt/vc/include


%ldconfig_scriptlets libs


%files libs
%doc LICENCE
%{_mandir}/man1/*.1*
%{_mandir}/man7/*.7*
%dir %{_libdir}/vc
%dir /opt/vc
/opt/vc/lib
%config %{_sysconfdir}/ld.so.conf.d/%{name}-%{_lib}.conf
%{_udevrulesdir}/10-vchiq.rules
%{_libdir}/vc/libbcm_host.so
%{_libdir}/vc/libdebug_sym.so
%{_libdir}/vc/libdtovl.so
%{_libdir}/vc/libvchiq_arm.so
%{_libdir}/vc/libvcos.so
%ifarch armv7hl
%{_libdir}/vc/libEGL.so
%{_libdir}/vc/libGLESv2.so
%{_libdir}/vc/libOpenVG.so
%{_libdir}/vc/libWFC.so
%{_libdir}/vc/libbrcmEGL.so
%{_libdir}/vc/libbrcmGLESv2.so
%{_libdir}/vc/libbrcmOpenVG.so
%{_libdir}/vc/libbrcmWFC.so
%{_libdir}/vc/libcontainers.so
%{_libdir}/vc/libmmal.so
%{_libdir}/vc/libmmal_components.so
%{_libdir}/vc/libmmal_core.so
%{_libdir}/vc/libmmal_util.so
%{_libdir}/vc/libmmal_vc_client.so
%{_libdir}/vc/libopenmaxil.so
%{_libdir}/vc/libvcsm.so
%{_libdir}/vc/plugins/reader_asf.so
%{_libdir}/vc/plugins/reader_avi.so
%{_libdir}/vc/plugins/reader_binary.so
%{_libdir}/vc/plugins/reader_flv.so
%{_libdir}/vc/plugins/reader_metadata_id3.so
%{_libdir}/vc/plugins/reader_mkv.so
%{_libdir}/vc/plugins/reader_mp4.so
%{_libdir}/vc/plugins/reader_mpga.so
%{_libdir}/vc/plugins/reader_ps.so
%{_libdir}/vc/plugins/reader_qsynth.so
%{_libdir}/vc/plugins/reader_raw_video.so
%{_libdir}/vc/plugins/reader_rcv.so
%{_libdir}/vc/plugins/reader_rtp.so
%{_libdir}/vc/plugins/reader_rtsp.so
%{_libdir}/vc/plugins/reader_rv9.so
%{_libdir}/vc/plugins/reader_simple.so
%{_libdir}/vc/plugins/reader_wav.so
%{_libdir}/vc/plugins/writer_asf.so
%{_libdir}/vc/plugins/writer_avi.so
%{_libdir}/vc/plugins/writer_binary.so
%{_libdir}/vc/plugins/writer_dummy.so
%{_libdir}/vc/plugins/writer_mp4.so
%{_libdir}/vc/plugins/writer_raw_video.so
%{_libdir}/vc/plugins/writer_simple.so
%endif

%files devel
%{rpmmacrodir}/macros.%{name}
%{_includedir}/vc/*
%{_datadir}/pkgconfig/*.pc
%{_libdir}/vc/pkgconfig/*.pc
/opt/vc/include


%files static
%ifarch armv7hl
%{_libdir}/vc/libEGL_static.a
%{_libdir}/vc/libGLESv2_static.a
%{_libdir}/vc/libkhrn_client.a
%{_libdir}/vc/libkhrn_static.a
%{_libdir}/vc/libvcilcs.a
%endif
%{_libdir}/vc/libdebug_sym_static.a
%{_libdir}/vc/libvchostif.a



%files utils
%ifarch armv7hl
%{_bindir}/containers_check_frame_int
%{_bindir}/containers_datagram_receiver
%{_bindir}/containers_datagram_sender
%{_bindir}/containers_dump_pktfile
%{_bindir}/containers_rtp_decoder
%{_bindir}/containers_stream_client
%{_bindir}/containers_stream_server
%{_bindir}/containers_test
%{_bindir}/containers_test_bits
%{_bindir}/containers_test_uri
%{_bindir}/containers_uri_pipe
%{_bindir}/mmal_vc_diag
%{_bindir}/raspistill
%{_bindir}/raspivid
%{_bindir}/raspividyuv
%{_bindir}/raspiyuv
%{_bindir}/vcsmem
%endif
%{_bindir}/dtmerge
%{_bindir}/dtoverlay
%{_bindir}/dtoverlay-post
%{_bindir}/dtoverlay-pre
%{_bindir}/dtparam
%{_bindir}/tvservice
%{_bindir}/vcgencmd
%{_bindir}/vchiq_test
%{_bindir}/vcmailbox


%files demo-source
%dir %{_usrsrc}/%{name}-demo-source
%{_usrsrc}/%{name}-demo-source/*



%changelog
* Mon Dec 06 2021 Stef Walter <stefw@redhat.com> - 2021206-1.20211206194915589553.master
- Development snapshot (8439acda)

* Mon Dec 06 2021 Stef Walter <stefw@redhat.com> - 2021206-1.20211206194755547599.master.0.g59da5d5
- Development snapshot (59da5d5f)

* Mon Dec 06 2021 Stef Walter <stefw@redhat.com> - 2021206-1.20211206194711628327.master.0.g59da5d5
- Development snapshot (59da5d5f)

* Tue Dec 29 2020 Damian Wrobel <dwrobel@ertelnet.rybnik.pl> - 20201130-0.git093b30b
- Update snapshot

* Tue Sep 22 2020 Damian Wrobel <dwrobel@ertelnet.rybnik.pl> - 20200813-2.gitf73fca0
- Change installation of ld.conf.d drop-in configuration file

* Mon Sep 14 2020 Damian Wrobel <dwrobel@ertelnet.rybnik.pl> - 20200813-1.gitf73fca0
- Update snapshot
- Fix build error on aarch64
- Generate raspberrypi-vc-libs.conf on the fly

* Mon Aug 03 2020 Nicolas Chauvet <kwizart@gmail.com> - 20200727-1.git3e59217
- Update snapshot

* Mon May 06 2019 Leigh Scott <leigh123linux@gmail.com> - 20190415-2.gitff2bd45
- Rebuild to fix rpi release tag

* Mon Apr 29 2019 Andrew Bauer <zonexpertconsulting@outlook.com> - 20190415-1.gitd574b51
- update package to April 15 commit ff2bd45

* Thu Dec 20 2018 Andrew Bauer <zonexpertconsulting@outlook.com> - 20181108-3.gitd574b51
- Build with BUILD_STATIC_LIBS ON

* Mon Dec 17 2018 Andrew Bauer <zonexpertconsulting@outlook.com> - 20181108-2.gitd574b51
- Build with BUILD_SHARED_LIBS OFF

* Sat Nov 10 2018 Andrew Bauer <zonexpertconsulting@outlook.com> - 20181108-1.gitd574b51
- Refactor for RPM Fusion
- See RFBZ 5074

* Wed Oct 10 2018 Vaughan <devel at agrez dot net> - 20181010-1.de4a7f2
- Sync to latest git revision: de4a7f2e3c391e2d3bc76af31864270e7802d9ac
- Add systemd build requires

* Mon Aug 27 2018 Vaughan <devel at agrez dot net> - 20180827-1.4228b6c
- Sync to latest git revision: 4228b6c1168e92b2e7cfe93a8aab03e4e75869b8

* Wed Aug 01 2018 Vaughan <devel at agrez dot net> - 20180801-1.f74ea7f
- Refactor spec file
- Add /opt/vc compatibility links
- Sync to latest git revision: f74ea7fdef9911904e269127443cd8a608abeacc

* Wed Jul 04 2018 Vaughan <devel at agrez dot net> - 20180704-1.409dfcd
- Sync to latest git revision: 409dfcd90bae0a09b1b8c1f718a532728d26cde2
- Misc spec cleanups / refactoring
- Add vchiq udev rule (Source2)

* Mon Jun 18 2018 Vaughan <devel at agrez dot net> - 20180618-1.2448644
- Sync to latest git revision: 2448644657e5fbfd82299416d218396ee1115ece

* Mon Mar 19 2018 Vaughan <devel at agrez dot net> - 20180319-1.eb3e6d7
- Sync to latest git revision: eb3e6d7b3d2ae585318c1c16055e3cecedceee4b

* Mon Feb 05 2018 Vaughan <devel at agrez dot net> - 20180205-1.fd98fcd
- Sync to latest git revision: fd98fcd64321e7195aee84ddda0d6e4e6c1f97f1

* Tue Dec 19 2017 Vaughan <devel at agrez dot net> - 20171219-1.3cd60d4
- Sync to latest git revision: 3cd60d45bc7c9d3ec8daee574bc99027cb1bab9e

* Thu Nov 02 2017 Vaughan <devel at agrez dot net> - 20171102-1.212184f
- Sync to latest git revision: 212184f0f1fdf76eff31e3875fdeb2b7980cd5cb

* Sun Sep 24 2017 Vaughan <devel at agrez dot net> - 20170924-1.a797602
- Sync to latest git revision: a7976021a89451de0d008aa48f16c4e88872899b

* Sat Jul 22 2017 Vaughan <devel at agrez dot net> - 20170722-1.9aab149
- Sync to latest git revision: 9aab1498b531b50585b206232d6baea64c0789f7

* Thu Jun 01 2017 Vaughan <devel at agrez dot net> - 20170601-1.
- Sync to latest git revision: 126f3de96f1c7d477a02d703fc285528cbce0540

* Sat May 06 2017 Vaughan <devel at agrez dot net> - 20170418-2.b8bdcc0
- Fix pkgconfig file glesv2.pc conflicts with mesa-libGLES-devel

* Tue Apr 18 2017 Vaughan <devel at agrez dot net> - 20170418-1.b8bdcc0
- Fix pkgconfig files
- Sync to latest git revision: b8bdcc0ed922a564f117e6a9a97ebbceab0b4024

* Sun Feb 05 2017 Vaughan <devel at agrez dot net> - 20170205-1.0f015ea
- Sync to latest git revision: 0f015eaa17add5bca00ecf8a354ea62e19bd7920

* Mon Jan 02 2017 Vaughan <devel at agrez dot net> - 20170102-1.bb15afe
- Sync to latest git revision: bb15afe33b313fe045d52277a78653d288e04f67

* Wed Oct 12 2016 Vaughan <devel at agrez dot net> - 20161012-1.2350bf2
- Sync to latest git revision: 2350bf2511fa49e177fb35c9613eef1b657a7506

* Mon Oct 03 2016 Vaughan <devel at agrez dot net> - 20161003-1.4dc8230
- Sync to latest git revision: 4dc8230536c919f0b3c833476bc9d0454c53977e

* Tue Sep 20 2016 Vaughan <devel at agrez dot net> - 20160920-1.a1b89e9
- Sync to latest git revision: a1b89e91f393c7134b4cdc36431f863bb3333163
- Update Patch0

* Thu Jun 16 2016 Vaughan <devel at agrez dot net> - 20160616-1.8daf8dd
- Sync to latest git revision: 8daf8dd493ecd25ceda075cd6ffa646193f00edb

* Sat Jun 04 2016 Vaughan <devel at agrez dot net> - 20160604-1.7c026fa
- Sync to latest git revision: 7c026fa7a4ded2c525916cc853a32731c072ed1e
- Add pkgconfig files to libs-devel

* Thu Apr 28 2016 Vaughan <devel at agrez dot net> - 20160428-1.17c28b9
- Sync to latest git revision: 17c28b9d1d234893b73adeb95efc4959b617fc85
- Update raspberrypi-vc-demo-source-path-fixup.patch
- Re-enable optflag -Wp,-D_FORTIFY_SOURCE=2 (fixed upstream)
- Clean up old Provides

* Tue Mar 22 2016 Vaughan <devel at agrez dot net> - 20160321-1.2f56a29
- Sync to latest git revision: 2f56a2943a9eb8420df52ccf91f5a1c5a70e8713
  Includes new dtoverlay utility
- Disable optflag -Wp,-D_FORTIFY_SOURCE=2

* Sun Mar 06 2016 mrjoshuap <jpreston at redhat dot com> - 20160305-1.8369e39
- Sync to latest git revision: 8369e390999f4a7c3bc57e577247e0dd502c51f7

* Fri Feb 05 2016 Vaughan <devel at agrez dot net> - 20160205-1.2a4af21
- Sync to latest git revision: 2a4af2192c0e161555fdb2a12e902b587166c4a6

* Sat Dec 12 2015 Vaughan <devel at agrez dot net> - 20151212-1.cfa3df1
- Sync to latest git revision: cfa3df1420a1839eb4a1da12e744a4beb8e7e7b6

* Sun Nov 29 2015 Vaughan <devel at agrez dot net> - 20151128-1.8d14732
- Sync to latest git revision: 8d14732f45f2aa204fdec599c69a9bdab4583247

* Fri Nov 06 2015 Vaughan <devel at agrez dot net> - 20151106-1.888945b
- Sync to latest git revision: 888945b683a4b8780adb3c217bd9a2a1a5899ef8

* Thu Sep 24 2015 Vaughan <devel at agrez dot net> - 20150903-1.40e3778
- Sync to latest git revision: 40e377862410371a9962db79b81fd4f0f266430a

* Thu Sep 03 2015 Vaughan <devel at agrez dot net> - 20150903-1.fb11b39
- Sync to latest git revision: fb11b39d97371c076eef7c85bbcab5733883a41e

* Wed Aug 19 2015 Vaughan <devel at agrez dot net> - 20150819-1.b864a84
- Sync to latest git revision: b864a841e5a459a66a890c22b3a34127cd226238

* Sat Jun 20 2015 Vaughan <devel at agrez dot net> - 20150620-1.b834074
- Add Requires for bcm283x-firmware

* Sun May 31 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150531-501.gitb834074
- Git revision master b834074d0c0d9d7e64c133ab14ed691999cee990
  mmal_queue: Add sanity checking to avoid common queue errors
- Git revision master d0954df802d43ea7cc94481435188913f6a65eee
  Add MMAL to IL mapping for rawcam parameters

  * Tue May 26 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150526-502.gitd4aa617
- Remove the hard-coded provides.

* Tue May 26 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150526-501.gitd4aa617
- Git revision master d4aa617de3b196399bb8e2ce32e181768cb52179
   vcsm: Add ioctl for custom cache flushing

* Tue May 19 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150519-501.git9cc14b2
- Git revision master 9cc14b29288f913ef0e3286f4b3232bf73ab59d2
  vcsm: Update to header from kernel side

* Thu May 14 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150503-502.gitd280099
- Rebuild for F22.

* Sun May 03 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150503-501.gitd280099.sc20
- Git revision master d28009949fe97631373ae4e5ab9ba7ed61910ee7
  Merge pull request #241 from nubok/patch-1
  Added "all" target to hello_fft/makefile
- Git revision master 74a6acf296bd814760b4b33f31925087e2a55cc0
  Added "all" target to hello_fft/makefile
  Same patch as https://github.com/raspberrypi/firmware/pull/422 for the
   firmware repository: The reason, why I added a new target "all" is that
   without it, the script /opt/vc/src/hello_pi/rebuild.sh only builds
   hello_fft.bin, but not hello_fft_2d.bin.

* Wed Apr 29 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150429-501.gitd8f146a.sc20
- Git revision master d8f146af05c2b9cd92f9a426148376b349f744fd
  Merge pull request #240 from 6by9/master
  Zero copy, and buildme change for Pi2
- Git revision master e8707f827c0e4ae5de892ac700b5bdb649350a1a
  Enable VCSM in MMAL by default
- Git revision master da7cab9fac646de891d84b232d1e25df1b6a0505
  Alter buildme to use multiple jobs and install on a Pi2

* Fri Apr 24 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150424-501.git198b9ac.sc20
- Git revision master 198b9ac3bcc0b54f1563664870fe415f04b7b6b5
  Merge pull request #239 from thaytan/master
  Fix intra-refresh port parameter setting.
- Git revision master 41b2b2918f08fbf7603e6f52120fff5bb6cc802c
  Fix intra-refresh port parameter setting.
  check mmal_port_parameter_get() succeeds when getting
   the default intra refresh values. It fails on older firmware.
  Fixes #238

* Sat Apr 18 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150418gitb69f807-501.sc20
- Git revision master b69f807ce59189457662c2144a8e7e12dc776988
  Merge pull request #237 from MarkusMattinen/patch-1
  Fix typo in buildme shebang
- Git revision master 36a20b6d92790a530421cb319a83ff9be79509d3
  Fix typo in buildme shebang
  Fixes #176.

* Sun Apr 12 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150412gitb4f537b-501.sc20
- Git revision master b4f537beef05afbd4337b9ca309aaa8b984177be
  mmal: Pass dts in place of pts when pts is invalid
- Git revision master 3fda6f920d65e08e342eef51e2476313cd021410
  mmal: Plumb in OMX_IndexParamBrcmInterpolateMissingTimestamps

* Tue Mar 17 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150323git7650bcb-501.sc20
- Git revision master 7650bcbc9ba8f1c5e29be7726d184b31c2665c46
  Merge pull request #233 from jsonn/patch-1
  Use a more sensible check than a tautoligy
- Git revision master 9b45a317b0ab56e83dfc228b6cd5800a0078835f
  Merge pull request #234 from jsonn/patch-2
  Fix typo in header guard
- Git revision master c08f005953a73dc9dc16df08d46d1baeb8c3bf4c
  Fix typo in header guard
- Git revision master 83b9970709e1f004542d0fccadbb7ea48b879d48
  Use a more sensible check than a tautoligy

* Tue Mar 17 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150317gitdaad93e-501.sc20
- Git revision master daad93e972f2332555ca2dc7b5a27a89d52572d5
  Merge pull request #225 from 6by9/PR20150223
  Raspistill/vid: More annotate options, and stereoscopic support.
- Git revision master d1a46714827d1192b86c0447c2c266ee5bb833be
  dispmanx: Add stereoscopic flags to control 3d duplication behaviour

* Tue Mar 10 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150310gitbb5b28f-501.sc20
- Git revision master bb5b28fc534f4f10c42c1c245673b26217aa03df
  Merge pull request #226 from 6by9/PR20150310
  Add an error message for MMAL_EVENT_ERROR
- Git revision master 695e11ced1e286d945f7dfcebae484ef3848a830
  Add an error message for MMAL_EVENT_ERROR
  It is signalled by the camera when no data is received on the CSI-2
   bus. Handle it specifically to try and avoid a bundle of duplicate
   forum posts.
- Git revision master 0567cba5b7c4fe07cce4ed0f13b2abb846b29114
  tvservice: Add option to choose frame packed hdmi mode
- Git revision master a31c068cfbf3d79eca20e947a1eca39333be902d
  vchiq: Add version define to indicate synchronous support

* Mon Mar 09 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150309git041604e-501.sc20
- Git revision master 041604e47e73fb2a9a487ce6f446e9b2d2042546
  raspicam: Fix minor typo in RaspiTexUtil

* Sun Mar 08 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150308git2fa36bf-502.sc20
- Tidy-up raspberrypi-vc-demo-source-path-fixup.patch

* Sun Mar 08 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150308git2fa36bf-501.sc20
- Git revision master 2fa36bfebc63ed913f002dceca4e966b538ad879
  mmal: Add MVC as a video encoding
- Git revision master ee9e0e4a79f129ef6408041baeace9f79b8f4609
  firmware: hello_fft: Update to version 3
   See: http://www.aholme.co.uk/GPU_FFT/Main.htm

* Fri Feb 20 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150226git0de0b20-502.sc20
- Fix LICENCE file permissions.

* Fri Feb 20 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150226git0de0b20-501.sc20
- Git revision master 0de0b205ea94ab61c24ea515cd3935e37d41ac03.
  vdec3: preparation work for MVC.
- Git revision master 73b57a700702a0e85a4817fff1f5104f9119dc79
  Annotate: Add control of text size, colour, bg colour, and handle CR.
- Git revision master f309a963f9ed3a86805bb9f983d6f81e89041df7
  vcmailbox: Add utility app for driving mailbox interface from command line.

* Fri Feb 20 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150220git6f12209-501.sc20
- Git revision master 6f122099ca3ef1115c740f927a64ccf54ca576ba.
  tvservice: Clear 3d settings before switching to new hdmi mode.
- Git revision master 8efa5baddf63166b9d114ce34e1da10685a11ad6
  Annotate timelapse images with timestamp or datetime.

* Sat Feb 14 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150214gitc5341f0-501.sc20
- Git revision master c5341f09dc686c17966369485f7dd27f58dc081c.
  cmake: Add -fPIC to avoid linking issues with Pi2 compile flags.
- Drop -fPIC. (Upstream has added it to cmake flags.)
- Move raspberrypi-vc-firmware to standalone package.

* Thu Feb 12 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150212git47bd0f0-501.sc20
- Updated firmware to commit 47bd0f0f46bc053d8e21655e3a69c4a73ae19b41.
- Updated userland to commit ddf78b2975c9d2f7511a16ca46ba0dfacd627006.

* Wed Feb 11 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150207gitd10602a-502.sc20
- Build with -fPIC.

* Sat Feb 07 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150207gitd10602a-501.sc20
- Updated firmware to commit d10602a5f3f3788ed673d98e3dec2af25666365d.
- Updated userland to commit 3893680f941b79b839c3313378aacb3dd0fc60ab.

* Thu Feb 05 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150205git0dad7b9-501.rpfr20
- Updated firmware to commit 0dad7b957c549ec3ee6bd142dcce03db186d6979.

* Wed Feb 04 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150204git28f1f25-501.rpfr20
- Updated firmware to commit 28f1f25e26b33c243c833ff89b70eae5a3b2467c.

* Fri Jan 30 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150130git9b068fe-501.rpfr20
- Updated firmware to commit 9b068fe44503f564579a25fd849df4ec784f9d4d.
- Updated userland to commit 3b81b91c18ff19f97033e146a9f3262ca631f0e9.

* Tue Jan 27 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150127gitd7c798d-501.rpfr20
- Updated firmware to commit d7c798d33ac7bf9474fcbc6be235cd5988d258a7.
- Updated userland to commit 8f542a1647e6f88f254eadd9ad6929301c81913b.

* Wed Jan 21 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150123git90ed5e5-501.rpfr20
- Updated firmware to commit 90ed5e5a7338d5c9d7aaa3306f92aac51ad20cc7.

* Wed Jan 21 2015 Clive Messer <clive.messer@squeezecommunity.org> - 20150121git6efbc2e-501.rpfr20
- Updated firmware to commit 6efbc2e7811189ee497dc5d676819661031e11e3.
- Updated userland to commit 6f530690af1b6bfc0eab463a804be7bf24fb8d4a.

* Thu Dec 18 2014 Clive Messer <clive.messer@squeezecommunity.org> - 20141218git833534ca-501.rpfr20
- Updated firmware to commit 833534cacc4bd0ce1ed2c077bb42aa466c468536.
- Updated userland to commit fed4730aebc329187894e3d8c7aa1e2943a8fdc1.

* Thu Dec 11 2014 Clive Messer <clive.messer@squeezecommunity.org> - 20141211git5f1b910-501.rpfr20
- Updated firmware to commit 5f1b9100dd340125ebc8a96a8781d4497ea006f6
- Updated userland to commit 4333d6d023a1f0dcc763d0706a1fe6523f9b6005

* Tue Nov 25 2014 Clive Messer <clive.messer@squeezecommunity.org> - 20141125gitf56e48c-501.rpfr20
- Updated firmware to commit f56e48c00b30a985ed68306348fc493bf6050f6b

* Sat Nov 22 2014 Clive Messer <clive.messer@squeezecommunity.org> - 20141122git1513cf8-501.rpfr20
- Updated firmware to commit 1513cf89c1fa211e900c23fb4a8b4da73bfd7102

* Sun Nov 16 2014 Clive Messer <clive.messer@squeezecommunity.org> - 20141116gita54afb6-501.rpfr20
- Updated firmware to commit a54afb6fe333cd1ae72170d2a452ae94d428b9c7
- Updated userland to commit 4333d6d023a1f0dcc763d0706a1fe6523f9b6005

* Fri Oct 03 2014 Clive Messer <clive.messer@squeezecommunity.org> - 20141003gitf2275b9-502.rpfr20
- Add 'Provides: libcontainers.so'.
- Add 'Provides: libmmal_components.so'.

* Fri Oct 03 2014 Clive Messer <clive.messer@squeezecommunity.org> - 20141003gitf2275b9-501.rpfr20
- Updated firmware to latest commit f2275b92477d1a01f45f321d648f0eeeeeb0a67e
- Updated userland to latest commit 44c48e076d1a62180c82f490ac2c8d95b0eff2e7

* Sat Sep 13 2014 Clive Messer <clive.messer@squeezecommunity.org> - 20140913gitb465bdb-501.rpfr20
- Updated firmware to latest commit b465bdb633003339da911bc8df4be4552a46b26c
- Updated userland to latest commit 0cbcb3a67f39b0522e4413207481906595b3591b

* Tue Aug 26 2014 Clive Messer <clive.messer@squeezecommunity.org> - 20140826git6eda68a-501.rpfr20
- Updated firmware to latest commit 6eda68af0e3f0897c5b72a3d44003f16ecdc9110
- Updated userland to latest commit d9a999f1e08e7f5311102c4e5d2961685da38820

* Wed Aug 13 2014 Clive Messer <clive.messer@squeezecommunity.org> - 20140813git43c5b2f-501.rpfr20
- Updated firmware to latest commit 43c5b2fc9bdb0a43ba67661b8677445e71ae9e82
  kernel/libs: VCHIQ: Make service closure fully synchronous
   With these patches, calls to vchiq_close_service and vchiq_remove_service
    won't return until any associated callback have been delivered to the
    callback thread.
  firmware: video_render: Add parameter for setting the colourspace
   Only applicable for non-opaque buffers.
  firmware: gpioman: Allow oscillator to be selected as a clock source
  firmware: image_decode: huffman and quantization tables shouldn't trigger
   'keep all following'.
   See: http://forum.stmlabs.com/showthread.php?tid=14839
  userland: hello_jpeg: Fix decode fail when width/height can't be parsed
   from first 80K block.
  firmware: video_render: Fix for stereo rendering when crop height is not
   populated.

* Sun Aug 10 2014 Clive Messer <clive.messer@squeezecommunity.org> - 20140810gitdf36e8d-501.rpfr20
- Add 'Provides: libvcsm.so' to libs sub-package.
- updated to firmware/userland to latest commit

* Wed Jul 02 2014 Andrew Greene <andrew.greene@senecacollege.ca> - 20140630git1682505-19.rpfr20
- updated to firmware/userland to latest commit

* Tue Jun 24 2014 Andrew Greene <andrew.greene@senecacollege.ca> - 20140618git462f3e3-18.rpfr20
- updated userland and firmware to latest commits

* Tue Jun 17 2014 Andrew Greene <andrew.greene@senecacollege.ca> - 20140616git5bb0317-17.rpfr20
- updated firmware to latest commit

* Fri Jun 13 2014 Andrew Greene <andrew.greene@senecacollege.ca> - 20140611gite45a4a2-16.rpfr20
- updated userland and firmware to latest commit

* Wed May 21 2014 Andrew Greene <andrew.greene@senecacollege.ca> - 20140516git97082b6-15.rpfr20
- Updated firmware and userland to latest commit also added missing commit date
  to userland

* Tue Apr 29 2014 Andrew Greene <andrew.greene@senecacollege.ca> - 20140428git316b922-14.rpfr20
- updated to latest commit

* Thu Apr 10 2014 Andrew Greene <andrew.greene@senecacollege.ca> - 20140117git940dc3b-13.rpfr20
- Added userland source files to build vc-demos from source

* Thu Mar 27 2014 Andrew Greene <andrew.greene@senecacollege.ca> - 20140117git940dc3b-12.rpfr20
- uncommented vc header patch

* Tue Jan 28 2014 Andrew Greene <andrew.greene@senecacollege.ca> - 20140117git940dc3b-8.rpfr20
- Added provides gl2.h to lib-devel

* Wed Jan 22 2014 Andrew Greene <andrew.greene@senecacollege.ca> - 20140117git940dc3b-7.rpfr20
- Initial build for pidora 2014 updated to latest commit

* Fri Nov 29 2013 Andrew Greene <andrew.greene@senecacollege.ca> - 20131128gitf7e9bcd-6.rpfr19
- updated to latest commit

* Mon Oct 28 2013 Andrew Greene <andrew.greene@senecacollege.ca> - 20131018git4c14569-5.rpfr18
- Updated to latest commit

* Thu Oct 17 2013 Andrew Greene <andrew.greene@senecacollege.ca> - 20131012git5113ce6-4.rpfr19
- Initial build for Pidora 19

* Wed Oct 16 2013 Andrew Greene <andrew.greene@senecacollege.ca> - 20131012git5113ce6-3.rpfr18
- Updated to latest commit

* Mon Sep 30 2013 Andrew Greene <andrew.greene@senecacollege.ca> - 20130918gitfadc4cb-2.rpfr18
- Added missing firmware files

* Thu Sep 19 2013 Andrew Greene <andrew.greene@senecacollege.ca> - 20130918gitfadc4cb-1.rpfr18
- Updated to latest commit

* Mon Sep 16 2013 Andrew Greene <andrew.greene@senecacollege.ca> - 20130910git7d8a762-1.rpfr18
- Updated to latest firmware

* Wed Aug 21 2013 andrew.greene@senecacollege.ca - 20130819git5b37b2a-1.rpfr18
- Updated to latest commit

* Fri Aug 16 2013 andrew.greene@senecacollege.ca - 20130815gite0590d6-1.rpfr18
- Updated to latest commit

* Mon Jul 15 2013 andrew.greene@senecacollege.ca - 20130711git245f716-3.rpfr18
- updated to latest commit moved header/lib files to subdirectory to deal with
  mesa lib conflicts and khrplatform conflicts

* Wed Jul 03 2013 andrew.greene@senecacollege.ca - 20130702gita36d33d-2.rpfr18
- moved conflicting headers to a sub dir and included a ld.so.conf.d file for
  conflicting libs

* Tue Jul 02 2013 andrew.greene@senecacollege.ca - 20130702gita36d33d-1.rpfr18
- Added provides for conflicts with mesa-libEGL-devel libs and updated firmware
  to latest commit

* Tue Jun 11 2013 andrew.greene@senecacollege.ca - 20130607git0d1b1d8-2.rpfr18
- updated to latest commit

* Wed May 15 2013 Chris Tyler <chris@tylers.info> - 20130415git1c339b1-1.rpfr18
- Updated to upstream, added suid on utils

* Fri Apr 19 2013 andrew.greene@senecacollege.ca - 20130410git7fcb9d3-2.rpfr18
- Included provides for libs libmmal_core and libmmal_util these are needed for vc-utils

* Tue Apr 16 2013 andrew.greene@senecacollege.ca - 20130410git7fcb9d3eb2-1.rpfr18
- Updated to latest version changed vchost_config.h location

* Sat Mar 02 2013 andrew.greene@senecacollege.ca - 20121125git7e9ac50-7.rpfr18
- Copied missing header file to the correct location vchost_config.h vcos_platform_types.h and vcos_platform.h

* Fri Mar 01 2013 andrew.greene@senecacollege.ca - 20121125git7e9ac50-4.rpfr18
- rebuilt for armv6hl

* Fri Mar 01 2013 andrew.greene@senecacollege.ca - 20121125git7e9ac50-3.rpfr18
- Added a provides tag

* Tue Nov 27 2012 Andrew Greene <andrew.greene@senecacollege.ca> - 20121125git7e9ac50-2.rpfr18
- Updated package release tag for rpfr18

* Tue Nov 27 2012 Chris Tyler <chris@tylers.info> - 20121125git7e9ac50-2.rpfr17
- Added provides for library subpackage
- Added softfp/hardfp binary selection

* Sun Nov 25 2012 Chris Tyler <chris@tylers.info> - 20121125git7e9ac50-1.rpfr17
- Updated to upstream

* Wed Sep 26 2012 Chris Tyler <chris@tylers.info> - 20120926gitb87bc42-1.rpfr17
- Updated to upstream

* Mon Aug 13 2012 Chris Tyler <chris@tylers.info> - 20120813gitcb9513f-1.rpfr17
- Updated to upstream
- Merged raspberrypi-firmware (now named raspberrypi-vc-firmware)

* Wed Aug 08 2012 Chris Tyler <chris@tylers.info> - 20120727git0d88fba-1.rpfr17
- Updated to upstream

* Wed Jul 04 2012 Chris Tyler <chris@tylers.info> - 20120703git0671d60-2.rpfr17
- Path and patch fixups

* Wed Jul 04 2012 Chris Tyler <chris@tylers.info> - 20120703git0671d60-1.rpfr17
- Updated to current upstream, adjusted for git commit in version

* Mon Mar 05 2012 Chris Tyler <chris@tylers.info> - 20120217-4
- Added path fixup for demo source code

* Mon Mar 05 2012 Chris Tyler <chris@tylers.info> - 20120217-3
- Fixed up move from vc/ subdir in /usr/include.

* Mon Mar 05 2012 Chris Tyler <chris@tylers.info> - 20120217-2
- Removed strip on libilclient.a, moved ilclient.h

* Tue Feb 21 2012 - Chris Tyler <chris.tyler@senecacollege.ca> - 20120217-1
- Initial packaging
