import json
import math
import cadquery as cq

from .components import *
from .geometry_contract import build_layout


def run_translation(instance_path):
    with open(instance_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    # Layout is the single source of truth for rows, frame positions,
    # beam levels, brace spacing, and component counts.
    layout = build_layout(data)
    W, H, D = layout.width, layout.height, layout.depth
    bay_count = layout.bay_count
    comp_map = {component["type"]: component["parameters"] for component in data["components"]}
    col_p, beam_p, brac_p = (
        comp_map["column"],
        comp_map["beam"],
        comp_map["bracing"],
    )
    panel_thick = 20.0

    assembly = cq.Assembly(name="Tectonic_Racking_System")

    col_shape = create_omega_column(col_p["width"], col_p["depth"], col_p["thickness"], H)
    beam_shape = create_box_beam(beam_p["width"], beam_p["height"], W - col_p["width"])
    base_plate = create_base_plate(col_p["width"], col_p["depth"])
    panel_shape = create_panel(W - col_p["width"] - 10, D, panel_thick)

    for row_index, y_coords in enumerate(layout.rows):
        y_mid = (y_coords[0] + y_coords[1]) / 2

        for frame_index, x_off in enumerate(layout.frame_x):
            for y in y_coords:
                assembly.add(
                    base_plate,
                    loc=cq.Location(cq.Vector(x_off, y, 0)),
                    name=f"base_{row_index}_{frame_index}_{y}",
                )
                assembly.add(
                    col_shape,
                    loc=cq.Location(cq.Vector(x_off, y, 0)),
                    name=f"col_{row_index}_{frame_index}_{y}",
                    color=cq.Color("blue"),
                )

            if frame_index in (0, layout.bay_count):
                segs = layout.brace_segments
                seg_h = layout.brace_height / segs
                brac_len = math.sqrt(D**2 + seg_h**2)
                angle_deg = math.degrees(math.atan(seg_h / D))
                single_brac = create_bracing(
                    brac_len, brac_p["width"], brac_p["thickness"]
                )

                for segment in range(segs):
                    z_mid = layout.bracing_margin / 2 + segment * seg_h + seg_h / 2
                    base_angle = 90 - angle_deg
                    total_angle = base_angle if segment % 2 == 0 else -base_angle
                    assembly.add(
                        single_brac,
                        loc=cq.Location(
                            cq.Vector(x_off, y_mid, z_mid),
                            cq.Vector(1, 0, 0),
                            total_angle,
                        ),
                        name=f"zbrac_{row_index}_{frame_index}_{segment}",
                        color=cq.Color("gray"),
                    )

        for bay_index in range(layout.bay_count):
            x_center = layout.frame_x[bay_index] + W / 2
            for layer_index, z_beam in enumerate(layout.beam_z):
                assembly.add(
                    beam_shape,
                    loc=cq.Location(cq.Vector(x_center, y_coords[0], z_beam)),
                    name=f"bmf_{row_index}_{bay_index}_{layer_index}",
                    color=cq.Color("orange"),
                )
                assembly.add(
                    beam_shape,
                    loc=cq.Location(cq.Vector(x_center, y_coords[1], z_beam)),
                    name=f"bmr_{row_index}_{bay_index}_{layer_index}",
                    color=cq.Color("orange"),
                )

                z_panel = z_beam + beam_p["height"] / 2 + panel_thick / 2
                assembly.add(
                    panel_shape,
                    loc=cq.Location(cq.Vector(x_center, y_mid, z_panel)),
                    name=f"pnl_{row_index}_{bay_index}_{layer_index}",
                    color=cq.Color("white"),
                )

    return assembly
