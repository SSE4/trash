from conans import ConanFile, CMake, tools
import os


class wxWidgetsConan(ConanFile):
    name = "wxwidgets"
    description = "wxWidgets is a C++ library that lets developers create applications for Windows, Mac OS X, " \
                  "Linux and other platforms with a single code base"
    version = "3.1.0"
    git_branch = "build_cmake"
    root = "wxWidgets-%s" % git_branch
    license = "wxWindows Licence"
    url = "https://gitlab.internal.divx.com/conan/wxwidgets"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False],
               "webview": [True, False],
               "media": [True, False],
               "gl": [True, False],
               "secretstore": [True, False],
               "fPIC": [True, False]}
    default_options = "shared=False", "webview=False", "media=False", "gl=True", "secretstore=False", "fPIC=True"
    generators = "cmake"
    exports_sources = 'CMakeLists.txt'

    wx_lib_name_version = None
    wx_platform = None
    wx_compiler_prefix = None
    wx_libs_dir = None
    wx_lib_name_formats = []
    wx_lib_names = []
    wx_suffix = ""
    wx_prefix = ""
    wx_unicode_suffix = ""
    wx_debug_suffix = ""
    wx_build_dir = None
    wx_include_dir = None
    wx_compiler_include_dir = None
    wx_platform_include_dir = None
    wx_compiler_defines = []
    wx_version = None

    def system_requirements(self):
        if self.settings.os == "Linux":
            if tools.os_info.linux_distro == "ubuntu" or tools.os_info.linux_distro == "debian":
                arch = ''
                if self.settings.arch == "x86" and tools.detected_architecture() == "x86_64":
                    arch = ':i386'
                packages = ['libx11-dev',
                            'libglib2.0-dev',
                            'libgdk-pixbuf2.0-dev',
                            'libpango1.0-dev',
                            'libatk1.0-dev',
                            'libcairo2-dev',
                            'libgtk2.0-dev libglib2.0-dev',
                            'libgtk2.0-dev',
                            'libtiff-dev']
                if self.options.secretstore:
                    packages.append('libsecret-1-dev')
                if self.options.gl:
                    packages.append('libgl1-mesa-dev')
                if self.options.webview:
                    packages.extend(['libsoup2.4-dev', 'libwebkitgtk-3.0-dev', 'libwebkitgtk-dev'])
                if self.options.media:
                    packages.extend(['libgstreamer0.10-dev', 'libgstreamer-plugins-base0.10-dev'])
                installer = tools.SystemPackageTool()
                for package in packages:
                    installer.install(' '.join(('%s%s' % (i, arch) for i in package.split())))

    def config(self):
        pass
    
    def source(self):
        zip_name = "wxWidgets-%s-%s.zip" % (self.git_branch, self.version)
        url_format = "http://pkg.qcserver.internal.divx.com/wxwidgets/%s/%s"
        url = url_format % (self.version, zip_name)
        tools.download(url, zip_name)
        tools.unzip(zip_name, ".")
        os.unlink(zip_name)

        for patch in ["glx11.patch", "gstreamer.patch", "libxml.patch"]:
            url = url_format % (self.version, patch)
            tools.download(url, patch)
            tools.patch(base_path=self.root, patch_file=patch)
            os.unlink(patch)

    def build(self):
        cmake = CMake(self)
        cmake.definitions['wxBUILD_SHARED'] = self.options.shared
        # TODO : options to use system libraries?
        if self.settings.os != "Linux":
            # not supported on Linux for some reason
            cmake.definitions['wxUSE_LIBTIFF'] = 'builtin'
        cmake.definitions['wxUSE_LIBJPEG'] = 'builtin'
        cmake.definitions['wxUSE_LIBPNG'] = 'builtin'
        cmake.definitions['wxUSE_REGEX'] = 'builtin'
        cmake.definitions['wxUSE_EXPAT'] = 'builtin'
        cmake.definitions['wxUSE_ZLIB'] = 'builtin'
        cmake.definitions['wxUSE_OPENGL'] = self.options.gl
        cmake.definitions['wxUSE_MEDIACTRL'] = self.options.media
        cmake.definitions['wxUSE_WEBVIEW'] = self.options.webview
        cmake.definitions['wxUSE_SECRETSTORE'] = self.options.secretstore
        cmake.definitions['wxBUILD_PRECOMP'] = False
        cmake.definitions['CMAKE_POSITION_INDEPENDENT_CODE'] = self.options.fPIC
        if str(self.settings.compiler) in ['gcc', 'clang', 'apple-clang']:
            cflags = ''
            if self.settings.arch == "x86":
                cflags += ' -m32'
            if self.options.fPIC:
                cflags += ' -fPIC'
        if len(cflags) > 0:
            cmake.definitions['CMAKE_C_FLAGS'] = cflags
            cmake.definitions['CMAKE_CXX_FLAGS'] = cflags

        cmake.configure()
        cmake.build()

    def package(self):
        self.copy("include/*", ".", "%s" % self.root, keep_path=True)
        self.copy(pattern="lib/*/setup.h", dst="include/wx", keep_path=False)
        self.copy("*.lib", dst="lib", keep_path=False)
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.so", dst="lib", keep_path=False)
        self.copy("*.dylib", dst="lib", keep_path=False)
        self.copy("*.a", dst="lib", keep_path=False)

    def package_info(self):
        self.gather_wx_config()
        self.wx_lib_names = self.wx_expand_lib_name_vars(reversed(self.wx_lib_name_formats))
        self.cpp_info.libs = self.wx_lib_names
        if self.settings.os == "Windows":
            self.cpp_info.libs.extend(["comctl32", "rpcrt4"])
        if self.settings.os == "Linux":
            self.cpp_info.defines.append("__WXGTK__")
            self.cpp_info.libs.extend(['gtk-x11-2.0', 'gdk-x11-2.0', 'pangocairo-1.0', 'gdk_pixbuf-2.0', 'X11',
                                       'gio-2.0', 'pango-1.0', 'gobject-2.0', 'glib-2.0', 'pthread', 'dl'])
        if self.settings.os == "Macos":
            self.cpp_info.defines.extend(["__WXMAC__", "__WXOSX__", "__WXOSX_COCOA__"])
            self.cpp_info.exelinkflags.append("-framework Carbon")
            self.cpp_info.exelinkflags.append("-framework Cocoa")
            self.cpp_info.exelinkflags.append("-framework IOKit")
            self.cpp_info.exelinkflags.append("-framework ApplicationServices")
            self.cpp_info.exelinkflags.append("-framework CoreText")
            self.cpp_info.exelinkflags.append("-framework CoreGraphics")
            self.cpp_info.exelinkflags.append("-framework ImageIO")
            self.cpp_info.sharedlinkflags = self.cpp_info.exelinkflags

    def wx_expand_lib_name_vars(self, name_format_list):
        return [
            name_format.format(
                platform=self.wx_platform,
                version=self.wx_lib_name_version,
                unicode=self.wx_unicode_suffix,
                debug=self.wx_debug_suffix,
                prefix=self.wx_prefix,
                suffix=self.wx_suffix,
            ) for name_format in name_format_list]
        
    def gather_wx_config(self):
        v = self.version.split(".")

        if self.settings.os == "Windows":
            self.wx_platform = "msw"
            self.wx_prefix = "wx"
            self.wx_suffix = ""
            self.wx_lib_name_version = v[0] + v[1]
            expat_fmt = "wxexpat{debug}{suffix}"
            jpeg_fmt = "wxjpeg{debug}{suffix}"
            png_fmt = "wxpng{debug}{suffix}"
            regex_fmt = "wxregex{unicode}{debug}{suffix}"
            scintilla_fmt = "wxscintilla{debug}{suffix}"
            tiff_fmt = "wxtiff{debug}{suffix}"
            zlib_fmt = "wxzlib{debug}{suffix}"
        elif self.settings.os == "Linux":
            self.wx_platform = "gtk2"
            self.wx_prefix = "wx_"
            self.wx_suffix = "-%s.%s" % (v[0], v[1])
            self.wx_lib_name_version = ""
            expat_fmt = "wxexpat{debug}"
            jpeg_fmt = "wxjpeg{suffix}"
            png_fmt = "wxpng{suffix}"
            regex_fmt = "wxregex{unicode}{suffix}"
            scintilla_fmt = "wxscintilla{suffix}"
            tiff_fmt = "tiff"
            zlib_fmt = "wxzlib{suffix}"
        elif self.settings.os == "Macos":
            self.wx_platform = "osx_cocoa"
            self.wx_prefix = "wx_"
            self.wx_suffix = "-%s.%s" % (v[0], v[1])
            self.wx_lib_name_version = ""
            expat_fmt = "expat"
            jpeg_fmt = "wxpng{suffix}"
            png_fmt = "wxpng{suffix}"
            regex_fmt = "wxregex{unicode}{suffix}"
            scintilla_fmt = "wxscintilla{suffix}"
            tiff_fmt = "wxtiff{suffix}"
            zlib_fmt = "z"
        else:
            raise Exception("unsupported os %s" % self.settings.os)

        self.wx_lib_name_formats = [
            zlib_fmt,
            png_fmt,
            jpeg_fmt,
            tiff_fmt,
            "{prefix}base{version}{unicode}{debug}{suffix}",
            "{prefix}base{version}{unicode}{debug}_net{suffix}",
            "{prefix}base{version}{unicode}{debug}_xml{suffix}",
            "{prefix}{platform}{version}{unicode}{debug}_adv{suffix}",
            "{prefix}{platform}{version}{unicode}{debug}_aui{suffix}",
            "{prefix}{platform}{version}{unicode}{debug}_core{suffix}",
            "{prefix}{platform}{version}{unicode}{debug}_html{suffix}",
            "{prefix}{platform}{version}{unicode}{debug}_propgrid{suffix}",
            "{prefix}{platform}{version}{unicode}{debug}_qa{suffix}",
            "{prefix}{platform}{version}{unicode}{debug}_ribbon{suffix}",
            "{prefix}{platform}{version}{unicode}{debug}_richtext{suffix}",
            "{prefix}{platform}{version}{unicode}{debug}_stc{suffix}",
            "{prefix}{platform}{version}{unicode}{debug}_xrc{suffix}",
            expat_fmt,
            regex_fmt,
            scintilla_fmt
        ]
        if self.options.webview:
            self.wx_lib_name_formats.append("{prefix}{platform}{version}{unicode}{debug}_webview{suffix}")
        if self.options.gl:
            self.wx_lib_name_formats.append("{prefix}{platform}{version}{unicode}{debug}_gl{suffix}")
        if self.options.media:
            self.wx_lib_name_formats.append("{prefix}{platform}{version}{unicode}{debug}_media{suffix}")

        # Unicode should always be enabled
        self.wx_unicode_suffix = "u"

        if self.settings.build_type == "Debug":
            self.wx_debug_suffix = "d"
