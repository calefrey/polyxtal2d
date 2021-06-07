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