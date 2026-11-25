from mmppe.release_check import import_check, boot_check

def test_release_import_gate(): import_check()
def test_release_boot_gate(): boot_check()
