"""Patch for APScheduler to work with Python 3.12"""
import sys
import warnings
import importlib

def patch_apscheduler():
    """
    Apply a comprehensive patch to make APScheduler work with Python 3.12
    by patching pkg_resources and setuptools
    """
    if sys.version_info >= (3, 12):
        try:
            # Patch 1: Try to directly patch the module
            import pkg_resources
            import pkgutil
            
            if not hasattr(pkgutil, 'ImpImporter'):
                class DummyImpImporter:
                    pass
                pkgutil.ImpImporter = DummyImpImporter
                
                # Patch the register_finder function
                original_register_finder = pkg_resources.register_finder
                def patched_register_finder(importer_type, finder_maker):
                    if importer_type is pkgutil.ImpImporter:
                        return
                    return original_register_finder(importer_type, finder_maker)
                pkg_resources.register_finder = patched_register_finder
                
            print("✅ Successfully patched pkg_resources for Python 3.12 compatibility")
                
        except Exception as e:
            print(f"⚠️ Warning: Could not patch APScheduler: {e}")
            
            # Patch 2: Alternative approach - monkey patch the import system
            try:
                # Create a dummy version of pkg_resources if it's missing
                class DummyVersion:
                    def __init__(self, version_string):
                        self.version_string = version_string
                    def __str__(self):
                        return self.version_string
                
                class DummyDist:
                    def __init__(self, version):
                        self._version = version
                    def version(self):
                        return self._version
                        
                class DummyPkgResources:
                    def get_distribution(self, package_name):
                        return DummyDist(DummyVersion("0.0.0"))
                    
                    def register_finder(self, *args, **kwargs):
                        pass
                        
                    def register_loader_type(self, *args, **kwargs):
                        pass
                        
                # Only apply if pkg_resources is not available
                try:
                    import pkg_resources
                except ImportError:
                    sys.modules['pkg_resources'] = DummyPkgResources()
                    print("✅ Created dummy pkg_resources for Python 3.12 compatibility")
                    
            except Exception as e:
                print(f"⚠️ Warning: Could not apply alternative patch: {e}")
                warnings.warn("APScheduler may not work correctly with Python 3.12")
    else:
        # No patching needed for Python < 3.12
        pass