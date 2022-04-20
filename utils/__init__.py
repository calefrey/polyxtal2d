def region_sanity(region, x_lim, y_lim, vertices):
    """
    Returns true if all corners of the region are within the x and y limits
    """
    # basically just go through the region and return false if any point is outside the bounds
    x_check = [vertices[i][0] < x_lim and vertices[i][0] >= 0 for i in region]
    y_check = [vertices[i][1] < y_lim and vertices[i][1] >= 0 for i in region]
    # the all function returns true only if all the list items are true
    region_valid = all(x_check + y_check)
    return region_valid


def midpoints(region):  # list[list[float]]) -> list[list[float]]
    """
    takes in a region defined as a set of corner points and returns the midpoints of all the sides
    """
    output = []
    for i in range(1, len(region) + 1):
        i = i % len(region)  # wrap around
        p1 = region[i - 1]
        p2 = region[i]
        x = (p1[0] + p2[0]) / 2
        y = (p1[1] + p2[1]) / 2
        output.append([x, y])
    return output


def length_scale(
    stiffness: float = 370e9,
    strength: float = 1e5,
    crit_displacement: float = 1e-2,
    check: bool = False,
    mesh_size: float = 0.11,
    crack_length: float = 5,
    scientific: bool = False,
    log: bool = False,
):
    toughness = 0.5 * strength * crit_displacement
    result = stiffness * toughness / pow(strength, 2)
    if check:
        if result > 10 * mesh_size:
            pass  # this is fine
        else:
            raise ValueError(
                f"The length scale needs to be greater than 10x the mesh size, was {result:.1E}"
            )

        if result < 10 * crack_length:
            pass  # this is fine
        else:
            raise ValueError(
                f"The length scale needs to be smaller than 10x the crack length, was {result:.1E}"
            )
    if scientific:
        result = "{:.1E}".format(result)
    if log:
        print(result)
    return result


import time


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if "log_time" in kw:
            name = kw.get("log_name", method.__name__.upper())
            kw["log_time"][name] = int((te - ts) * 1000)
        else:
            print(f"{method.__name__}  {(te - ts) * 1000:.2f} ms")
        return result

    return timed


def add_crack(grain_array: dict, grain_centers: dict, x_max, y_min, y_max):
    import copy

    # create duplicate arrays to modify
    new_grain_array = copy.deepcopy(grain_array)
    new_grain_centers = copy.deepcopy(grain_centers)
    for key, value in grain_centers.items():
        x = value[0]
        y = value[1]
        if x < x_max and y_min < y < y_max:
            # Add a crack by deleting grain from the new arrays
            new_grain_array.pop(key)
            new_grain_centers.pop(key)
    return new_grain_array, new_grain_centers
