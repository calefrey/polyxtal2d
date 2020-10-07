from utils.bisector_scaling import scale


class grain:
    def __init__(self, vertices, vertIDs, idx):
        self.vertices = vertices
        self.vertIDs = vertIDs
        self.id = idx

    def blank(self):
        # make new instance to be manipulated later while the original remains intact
        return grain([], self.vertIDs, self.id)

    def scaled(self, distance=0.1):
        distance = distance * 1.154700538379252
        scaled_hex = self.blank()  # don't modify the original one
        scaled_hex.original = self
        scaled_hex.vertices = []
        for i in range(2, len(self.vertices) + 2):
            i = i % len(self.vertices)  # wrap around the list
            corner = scale(
                self.vertices[i - 2], self.vertices[i - 1], self.vertices[i], distance
            )
            scaled_hex.vertices.append(corner)
        return scaled_hex