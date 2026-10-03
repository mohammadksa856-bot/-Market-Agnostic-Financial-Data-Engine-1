from bundle_adapters import adapt_a_b
from bundle_adapters2 import adapt_c_f

def adapt_all(existing=None):
    adapt_a_b()
    return adapt_c_f()
