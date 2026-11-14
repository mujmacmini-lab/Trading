"""Registry for strategy specs. Each spec is a real function, so it is syntax-checked and testable;
build.py turns every spec into a self-contained strategies/sNNN.py file."""
SPECS = []


def strat(name, family, idea, **params):
    def deco(fn):
        SPECS.append({"fn": fn, "name": name, "family": family, "idea": idea, "params": params})
        return fn
    return deco
