
get_filename_component (VIDEOCORE_ROOT ../../../../ ABSOLUTE)
include (${VIDEOCORE_ROOT}/makefiles/cmake/global_settings.cmake)

include_directories (
   ${VCOS_ROOT}/{RTOS}
   ${VIDEOCORE_HEADERS_BUILD_DIR}
   ../../../../host_support/include
   ${VIDEOCORE_ROOT})

add_library(debug_sym ${SHARED} debug_sym.c)
add_library(debug_sym_static STATIC debug_sym.c)

install(TARGETS debug_sym DESTINATION ${LIBDIR})
install(TARGETS debug_sym_static DESTINATION ${LIBDIR})
install(FILES debug_sym.h DESTINATION include/interface/debug_sym)
