import streamlit as st
import matplotlib.pyplot as plt

def interpolate_point(p1, p2, fraction):
    """
    Linearly interpolate between two points p1 and p2 by a given fraction (0 to 1).
    If fraction=0, returns p1; if fraction=1, returns p2; 
    values in between yield a point along the line segment connecting p1 and p2.
    """
    return (p1[0] + fraction * (p2[0] - p1[0]),
            p1[1] + fraction * (p2[1] - p1[1]))

def get_scale_factor_for_midline(age, sex):
    """
    Returns a scaling factor to adjust midline electrode positions based on age and sex.
    - Younger ages compress distances toward Cz (less spread).
    - Female sex slightly reduces the spread by an additional factor.
    
    This is a hypothetical model:
    - At age 1, factor ~0.7 (70% of adult spacing)
    - By age 20, factor ~1.0 (full adult spacing)
    - For female, multiply by 0.95 to slightly reduce distances.
    """
    # Age-based scaling
    if age < 1:
        age_factor = 0.7
    elif age > 20:
        age_factor = 1.0
    else:
        # Linear interpolation between age 1 and 20
        # age=1 -> 0.7, age=20 -> 1.0
        age_factor = 0.7 + (1.0 - 0.7)*((age - 1)/19)
    
    # Sex-based scaling
    sex_factor = 0.95 if sex.lower() == 'female' else 1.0

    return age_factor * sex_factor

def get_midline_fractions(age, sex):
    """
    Compute the relative positions of midline electrodes as fractions along the nasion-inion line.
    Cz is fixed at 0.50 (the midpoint).
    Fpz, Fz, Pz, Oz are defined as offsets from Cz, then scaled by the factor from get_scale_factor_for_midline.
    
    Offsets:
    - Fpz: Cz - 0.40
    - Fz:  Cz - 0.30
    - Pz:  Cz + 0.20
    - Oz:  Cz + 0.40
    """
    cz_fraction = 0.50
    offsets = {
        'Fpz': -0.40,
        'Fz':  -0.30,
        'Pz':   0.20,
        'Oz':   0.40
    }

    scale = get_scale_factor_for_midline(age, sex)

    # Apply scaling to each offset
    fractions = {'Cz': cz_fraction}
    for label, offset in offsets.items():
        fractions[label] = cz_fraction + offset * scale

    return fractions

def compute_electrodes(age, sex, nasion_inion_distance, preauricular_distance):
    """
    Given age, sex, and head measurements (nasion-inion and preauricular distances),
    compute the electrode positions on the scalp.
    
    Steps:
    1. Define nasion and inion points along the vertical line.
    2. Define left and right preauricular points halfway down vertically.
    3. Get midline electrode fractions and place midline electrodes.
    4. Place lateral and temporal electrodes based on the midline electrode's vertical position.
    """
    # Nasion at the top (0,0), inion down along y-axis
    nasion = (0.0, 0.0)
    inion = (0.0, -nasion_inion_distance)

    # Preauricular points placed halfway down the nasion-inion distance
    mid_vertical = nasion_inion_distance * 0.5
    left_preauricular = (-preauricular_distance/2.0, -mid_vertical)
    right_preauricular = (preauricular_distance/2.0, -mid_vertical)

    # Compute midline electrode positions
    midline_fracs = get_midline_fractions(age, sex)
    electrodes = {}
    for label, frac in midline_fracs.items():
        electrodes[label] = interpolate_point(nasion, inion, frac)

    def place_lateral_electrodes(midline_label, left_label, right_label):
        """
        Place a pair of electrodes (left and right) aligned with a given midline electrode.
        We interpolate between the midline point and the left/right boundaries (ear level)
        to find the electrode positions laterally.
        """
        mid_x, mid_y = electrodes[midline_label]
        total_height = nasion_inion_distance
        # rel_y: fraction along nasion-inion line for vertical position
        rel_y = (mid_y - inion[1]) / total_height

        # Interpolate horizontal bounds at this vertical level
        left_bound = interpolate_point(inion, left_preauricular, rel_y)
        right_bound = interpolate_point(inion, right_preauricular, rel_y)

        # Place electrodes 30% from midline towards each ear
        left_elec_pos = interpolate_point((mid_x, mid_y), left_bound, 0.3)
        right_elec_pos = interpolate_point((mid_x, mid_y), right_bound, 0.3)

        electrodes[left_label] = left_elec_pos
        electrodes[right_label] = right_elec_pos

    # Place lateral electrodes from each midline reference
    place_lateral_electrodes('Fpz', 'Fp1', 'Fp2')
    place_lateral_electrodes('Fz', 'F3', 'F4')
    place_lateral_electrodes('Cz', 'C3', 'C4')
    place_lateral_electrodes('Pz', 'P3', 'P4')
    place_lateral_electrodes('Oz', 'O1', 'O2')

    def place_temporal_electrodes(y_label, left_label, right_label, fraction_from_mid=0.8):
        """
        Place temporal electrodes (like T7, T8) further laterally at a given fraction 
        from the midline electrode position towards the preauricular boundary.
        """
        mid_x, mid_y = electrodes[y_label]
        total_height = nasion_inion_distance
        rel_y = (mid_y - inion[1]) / total_height
        left_bound = interpolate_point(inion, left_preauricular, rel_y)
        right_bound = interpolate_point(inion, right_preauricular, rel_y)

        # Place temporal electrodes 80% towards the ears from midline electrode
        left_pos = interpolate_point((mid_x, mid_y), left_bound, fraction_from_mid)
        right_pos = interpolate_point((mid_x, mid_y), right_bound, fraction_from_mid)
        electrodes[left_label] = left_pos
        electrodes[right_label] = right_pos

    # Place temporal electrodes at Cz level
    place_temporal_electrodes('Cz', 'T7', 'T8')

    return electrodes, nasion, inion, left_preauricular, right_preauricular, nasion_inion_distance, preauricular_distance

# ---- Streamlit App ----

st.title("EEG Electrode Placement (2D)")

# Sidebar inputs for parameters
st.sidebar.header("Parameters")
age = st.sidebar.number_input("Age (years)", min_value=0.0, value=5.0, step=1.0)
sex = st.sidebar.selectbox("Sex", options=["male", "female"])
nasion_inion_distance = st.sidebar.number_input("Nasion-Inion distance (cm)", min_value=1.0, value=35.0)
preauricular_distance = st.sidebar.number_input("Preauricular distance (cm)", min_value=1.0, value=30.0)

# Compute electrode positions with given parameters
electrodes, nasion, inion, lpa, rpa, ni_dist, pa_dist = compute_electrodes(age, sex, nasion_inion_distance, preauricular_distance)

st.subheader("Electrode Coordinates")
for name, coord in electrodes.items():
    st.write(f"{name}: {coord}")

# Define the radius of the head circle based on both distances
# Here we take the average of the two dimensions and halve it again: (ni_dist + pa_dist)/4
# This ensures changing either measurement updates the circle size
radius = (ni_dist + pa_dist) / 4.0

fig, ax = plt.subplots(figsize=(6,6))

# Draw the head as a circle centered halfway along nasion-inion line.
# Using (0, -ni_dist/2.0) to roughly center the head in vertical direction.
head_circle = plt.Circle((0, -ni_dist/2.0), radius, color='lightblue', alpha=0.3)
ax.add_artist(head_circle)

# Plot electrodes on top
for name, (x,y) in electrodes.items():
    ax.scatter(x, y, c='r')
    ax.text(x, y, name, fontsize=9, ha='center', va='bottom', color='black')

# Plot reference points (nasion, inion, LPA, RPA)
ax.scatter([nasion[0], inion[0], lpa[0], rpa[0]],
           [nasion[1], inion[1], lpa[1], rpa[1]],
           c='b', marker='x')

ax.text(nasion[0], nasion[1], 'Nasion', fontsize=9, color='b', ha='center', va='bottom')
ax.text(inion[0], inion[1], 'Inion', fontsize=9, color='b', ha='center', va='top')
ax.text(lpa[0], lpa[1], 'LPA', fontsize=9, color='b', ha='right', va='center')
ax.text(rpa[0], rpa[1], 'RPA', fontsize=9, color='b', ha='left', va='center')

ax.set_title(f"2D Head Representation ({age}-yr-old {sex})")
ax.set_xlabel("X-position (cm)")
ax.set_ylabel("Y-position (cm)")
ax.set_aspect('equal', adjustable='box')
ax.grid(True)

# Display the plot in Streamlit
st.pyplot(fig)
