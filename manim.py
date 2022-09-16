# Tool for generating animations, used by 3blue1brown.
# Documentation available at https://docs.manim.community


from manim import *
import random
from scipy.spatial import Voronoi, voronoi_plot_2d, Delaunay

from utils import region_sanity

seed = 1134
size = 40

myText = lambda s, **kwargs: Text(s, font="Calibri", **kwargs)


# render with manim .\manim.py homogenous
class homogenous(Scene):
    def construct(self):
        ax = Axes(
            x_range=[0, size, 1],
            y_range=[0, size, 1],
            tips=False,
            x_length=7,
            y_length=7,
        ).to_edge(LEFT)
        self.play(Create(ax))

        t1 = (
            myText("Start with an array of points", font_size=22)
            .next_to(ax.get_edge_center(RIGHT), RIGHT)
            .shift(UP)
        )

        coords = []
        for i in range(0, size):
            x = i
            for j in range(0, size):
                if i % 2:
                    j = j + 0.5
                y = j
                coords.append([x, y])
        dots = [
            Dot(ax.coords_to_point(*coord), radius=0.02, color=BLUE) for coord in coords
        ]
        self.play(
            Create(VGroup(*dots)),
            FadeIn(t1),
            run_time=2,
        )
        self.wait()
        self.play(FadeOut(t1))

        t2 = (
            myText("Add some random noise", font_size=22)
            .next_to(ax.get_edge_center(RIGHT), RIGHT)
            .shift(UP)
        )

        random.seed(seed)

        new_coords = [
            [
                coord[0] + random.gauss(0, 0.25) * 0.5,
                coord[1] + random.gauss(0, 0.25) * 0.5,
            ]
            for coord in coords
        ]

        self.play(
            *[
                dot.animate.move_to(ax.coords_to_point(*new_coord))
                for dot, new_coord in zip(dots, new_coords)
            ],
            FadeIn(t2),
            run_time=2,
        )
        self.wait()
        self.play(FadeOut(t2))

        t3 = (
            myText(
                "Make a Voronoi tesselation.\nThese will be our grains.", font_size=22
            )
            .next_to(ax.get_edge_center(RIGHT), RIGHT)
            .shift(UP)
        )
        vor = Voronoi(new_coords)
        polygon_array = []
        for r_idx, region in enumerate(vor.regions):
            if (
                region
                and not -1 in region
                and region_sanity(region, size, size, vor.vertices)
            ):
                corners = [vor.vertices[i] + [0] for i in region if i >= 0]
                polygon = Polygon(
                    *[ax.coords_to_point(*corner) for corner in corners],
                    color=BLUE,
                    fill_opacity=0.5,
                    stroke_width=1,
                )
                polygon_array.append(polygon)

        # self.play(Create(polygon))
        self.play(Create(VGroup(*polygon_array)), FadeIn(t3), run_time=2)
        self.wait()

        self.play(FadeOut(t3))

        t4 = (
            myText(
                "Shrink the grains to provide space\nfor cohesive behavior",
                font_size=22,
            )
            .next_to(ax.get_edge_center(RIGHT), RIGHT)
            .shift(UP)
        )

        self.play(
            *[polygon.animate.scale(0.9) for polygon in polygon_array], FadeIn(t4)
        )
        self.wait()

        self.play(FadeOut(t4))

        # t5 = (
        #     myText(
        #         "Pick some grains to modify and\nchange their properties",
        #         font_size=22,
        #     )
        #     .next_to(ax.get_edge_center(RIGHT), RIGHT)
        #     .shift(UP)
        # )
        # self.play(
        #     *[
        #         polygon.animate.set_fill(color=PINK, opacity=0.5)
        #         for polygon in polygon_array
        #         if random.random() < 0.25
        #     ],
        #     FadeIn(t5),
        # )

        # t6 = myText(
        #     "Let the modified grains be\n25% weaker and 25% tougher",
        #     font_size=22,
        # ).next_to(t5, DOWN)

        # self.wait()
        # self.play(FadeIn(t6))
        # self.wait()
        # self.play(FadeOut(t5), FadeOut(t6))

        self.play(FadeOut(ax.axes), FadeOut(VGroup(*dots)))  # remove dots and axes

        # add crack
        precrack_text = myText("Add a precrack", font_size=22).next_to(
            ax.get_edge_center(RIGHT), RIGHT
        )
        x_max = size / 6
        # bounds of crack should be one grain in size, centered around the middle.
        halfway = size / 2
        y_min = halfway - 1
        y_max = halfway + 1
        self.play(
            FadeOut(
                *[
                    p
                    for p in polygon_array
                    if (
                        y_min < ax.point_to_coords(p.get_center())[1] < y_max
                    )  # y limits
                    and (ax.point_to_coords(p.get_center())[0] < x_max)  # x limits
                ]
            ),
            FadeIn(precrack_text),
        )
        self.wait()
        self.play(FadeOut(precrack_text))

        # displacements
        t7 = (
            myText(
                "Apply tension to the sample\nby pulling the top\nand pinning the bottom",
                font_size=22,
            )
            .next_to(ax.get_edge_center(RIGHT), RIGHT)
            .shift(UP)
        )

        BC1 = VGroup()
        for i in range(14):
            BC1 += Arrow(
                start=UP * 0.5, end=DOWN * 0.5, color=BLUE, tip_shape=ArrowSquareTip
            )
        BC1.arrange(RIGHT, buff=0.25)
        BC1.move_to(ax.get_edge_center(DOWN))

        BC2 = VGroup()
        for i in range(10):
            BC2 += Arrow(start=DOWN * 0.5, end=UP * 0.5, color=BLUE)
        BC2.arrange(RIGHT, buff=0.5)
        BC2.move_to(ax.get_edge_center(UP))

        self.play(FadeIn(BC1), FadeIn(BC2), FadeIn(t7))
        self.wait()


# render with manim .\manim.py hetero -n 14
class hetero(Scene):
    def construct(self):
        ax = Axes(
            x_range=[0, size, 1],
            y_range=[0, size, 1],
            tips=False,
            x_length=7,
            y_length=7,
        ).to_edge(LEFT)
        self.play(Create(ax))

        t1 = (
            myText("Start with an array of points", font_size=22)
            .next_to(ax.get_edge_center(RIGHT), RIGHT)
            .shift(UP)
        )

        coords = []
        for i in range(0, size):
            x = i
            for j in range(0, size):
                if i % 2:
                    j = j + 0.5
                y = j
                coords.append([x, y])
        dots = [
            Dot(ax.coords_to_point(*coord), radius=0.02, color=BLUE) for coord in coords
        ]
        self.play(
            Create(VGroup(*dots)),
            FadeIn(t1),
            run_time=2,
        )
        self.wait()
        self.play(FadeOut(t1))

        t2 = (
            myText("Add some random noise", font_size=22)
            .next_to(ax.get_edge_center(RIGHT), RIGHT)
            .shift(UP)
        )

        random.seed(seed)

        new_coords = [
            [
                coord[0] + random.gauss(0, 0.25) * 0.5,
                coord[1] + random.gauss(0, 0.25) * 0.5,
            ]
            for coord in coords
        ]

        self.play(
            *[
                dot.animate.move_to(ax.coords_to_point(*new_coord))
                for dot, new_coord in zip(dots, new_coords)
            ],
            FadeIn(t2),
            run_time=2,
        )
        self.wait()
        self.play(FadeOut(t2))

        t3 = (
            myText(
                "Make a Voronoi tesselation.\nThese will be our grains.", font_size=22
            )
            .next_to(ax.get_edge_center(RIGHT), RIGHT)
            .shift(UP)
        )
        vor = Voronoi(new_coords)
        polygon_array = []
        for r_idx, region in enumerate(vor.regions):
            if (
                region
                and not -1 in region
                and region_sanity(region, size, size, vor.vertices)
            ):
                corners = [vor.vertices[i] + [0] for i in region if i >= 0]
                polygon = Polygon(
                    *[ax.coords_to_point(*corner) for corner in corners],
                    color=BLUE,
                    fill_opacity=0.5,
                    stroke_width=1,
                )
                polygon_array.append(polygon)

        # self.play(Create(polygon))
        self.play(Create(VGroup(*polygon_array)), FadeIn(t3), run_time=2)
        self.wait()

        self.play(FadeOut(t3))

        t4 = (
            myText(
                "Shrink the grains to provide space\nfor cohesive behavior",
                font_size=22,
            )
            .next_to(ax.get_edge_center(RIGHT), RIGHT)
            .shift(UP)
        )

        self.play(
            *[polygon.animate.scale(0.9) for polygon in polygon_array], FadeIn(t4)
        )
        self.wait()

        self.play(FadeOut(t4))

        t5 = (
            myText(
                "Pick some grains to modify and\nchange their properties",
                font_size=22,
            )
            .next_to(ax.get_edge_center(RIGHT), RIGHT)
            .shift(UP)
        )
        self.play(
            *[
                polygon.animate.set_fill(color=PINK, opacity=0.5)
                for polygon in polygon_array
                if random.random() < 0.25
            ],
            FadeIn(t5),
        )

        t6 = myText(
            "Let the modified grains be\n25% weaker and 25% tougher",
            font_size=22,
        ).next_to(t5, DOWN)

        self.wait()
        self.play(FadeIn(t6))
        self.wait()

        self.play(FadeOut(ax.axes), FadeOut(VGroup(*dots)))  # remove dots and axes
        self.play(FadeOut(t5), FadeOut(t6))

        # add crack
        precrack_text = myText("Add a precrack", font_size=22).next_to(
            ax.get_edge_center(RIGHT), RIGHT
        )
        x_max = size / 6
        # bounds of crack should be one grain in size, centered around the middle.
        halfway = size / 2
        y_min = halfway - 1
        y_max = halfway + 1
        self.play(
            FadeOut(
                *[
                    p
                    for p in polygon_array
                    if (
                        y_min < ax.point_to_coords(p.get_center())[1] < y_max
                    )  # y limits
                    and (ax.point_to_coords(p.get_center())[0] < x_max)  # x limits
                ]
            ),
            FadeIn(precrack_text),
        )
        self.wait()
        self.play(FadeOut(precrack_text))

        # displacements
        t7 = (
            myText(
                "Apply tension to the sample\nby pulling the top\nand pinning the bottom",
                font_size=22,
            )
            .next_to(ax.get_edge_center(RIGHT), RIGHT)
            .shift(UP)
        )

        BC1 = VGroup()
        for i in range(14):
            BC1 += Arrow(
                start=UP * 0.5, end=DOWN * 0.5, color=BLUE, tip_shape=ArrowSquareTip
            )
        BC1.arrange(RIGHT, buff=0.25)
        BC1.move_to(ax.get_edge_center(DOWN))

        BC2 = VGroup()
        for i in range(10):
            BC2 += Arrow(start=DOWN * 0.5, end=UP * 0.5, color=BLUE)
        BC2.arrange(RIGHT, buff=0.5)
        BC2.move_to(ax.get_edge_center(UP))

        self.play(FadeIn(BC1), FadeIn(BC2), FadeIn(t7))
        self.wait()
