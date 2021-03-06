#!/usr/bin/env python
import sys, os, copy
from waflib import Node
from waflib.extras import symwaf2ic


def depends(ctx):
    ctx('symap2ic', 'src/logging')

    if ctx.options.with_flansch:
        ctx('flansch')


def options(opt):
    opt.load('g++')
    opt.load('boost')

    hopts = opt.add_option_group('Vmodule Options')
    hopts.add_withoption('flansch', default=False,
                   help='Enable/Disable flansch backend')
    hopts.add_withoption('tests', default=False,
                   help='Enable/Disable build of flyspi tests (changes dependencies -- use flag in setup)')


def configure(cfg):
    cfg.load('g++')
    cfg.load('boost')

    cfg.check_boost(lib='system thread serialization', uselib_store='BOOST4PYFLYSPI')
    cfg.check_boost(lib='program_options system thread serialization', uselib_store='BOOST4FLYSPITOOLS')

    cfg.check_cfg(package='libusb-1.0', args=['--cflags', '--libs'], uselib_store='USB')

    cfg.env.enable_flansch = cfg.options.with_flansch
    cfg.env.enable_tests = cfg.options.with_tests


def build(bld):
    flags = {
        "cxxflags" : [
            '-std=c++0x',
            '-g',
            '-O0',
            #'-pedantic',
            '-Wall',
            '-Wextra',
            '-Wno-c++0x-compat',
            '-Wno-c++11-compat',
            '-fPIC'
        ]
    }

    SOURCES = [
        'units/vmodule_base/source/vmodule.cpp',
        'units/vmodule_base/source/readhex.cpp',
        'units/flyspi/source/Vmodule_adc.cpp',
        'units/flyspi/source/Vmoduleusb.cpp',
        'units/flyspi/source/Vusbmaster.cpp',
        'units/flyspi/source/Vusbstatus.cpp',
        'units/flyspi/source/Vmemory.cpp',
        'units/flyspi/source/Vocpfifo.cpp',
        'units/flyspi/source/Vocpmodule.cpp',
        'units/flyspi/source/Vspiconfrom.cpp',
        'units/flyspi/source/Vspigyro.cpp',
        'units/flyspi/source/Vspigyrowl.cpp',
        'units/flyspi/source/Vspimodule.cpp',
        'units/flyspi/source/Vspiwireless.cpp',
        'units/flyspi/source/Vmux_board.cpp',
        #Spikey specific
        'units/flyspi/source/Vspikey.cpp',
        'units/flyspi/source/Vspidac.cpp',
        #ADC board specific
        'units/flyspi/source/Vspifastadc.cpp',
        'units/flyspi/source/Vlmh6518.cpp',
    ]

    vmodule_object_use = ['USB', 'logger_obj', 'vmodule_objects_inc', 'usbcomm']

    if bld.env.enable_flansch:
        flags['cxxflags'].append('-DWITH_FLANSCH')
        SOURCES.append('units/vmodule_base/source/Vmodulesim.cpp')
        vmodule_object_use.extend(['flansch_inc','flansch_software'])

    vflags = copy.copy(flags)
    vflags['cxxflags'].append('-fPIC')

    bld (
        export_includes = '. units/vmodule_base/source/ units/flyspi/source/',
        name = 'vmodule_objects_inc',
    )

    bld.objects(
		source = [
            'units/flyspi/source/usbcom.cpp',
            'units/flyspi/source/error_base.cpp',
        ],
        target = 'usbcomm',
        name   = 'usbcomm',
        use    = ['USB','logger_obj'],
        **flags
    )

    bld.objects(
        name = 'vmodule_objects',
        target   = 'vmodule_objects',
        source   = SOURCES,
        use      = vmodule_object_use,
        **flags
    )

    for filename in bld.path.ant_glob('units/flyspi/tools/*.cpp'):
        split = Node.split_path(filename.abspath())
        bld.program (
            target = os.path.splitext(split[len(split)-1])[0],
            source = [filename],
            use = ['BOOST4FLISPY', 'USB', 'BOOST4FLYSPITOOLS', 'vmodule_objects', 'logger_obj'],
            install_path = 'bin',
            **flags
        )

    if bld.env.enable_tests:
        bld(target          = 'flyspy-test',
            features        = 'cxx cxxprogram gtest',
            source          = bld.path.ant_glob('units/flyspi/test/*.cpp'),
            install_path    = os.path.join('bin', 'tests'),
            use             = [ 'vmodule_objects' ],
            cxxflags        = [
                    '-g', '-O0',
                    '-std=c++0x',
                    '-Wall',
                    '-Wextra',
            ])
