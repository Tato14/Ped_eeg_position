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
    Returns a scaling factor and a frontal shift based on age and sex.
    - At age 10: Full standard spacing (no scaling, no shift).
    - Under age 10: The electrodes shift more towards the front rather than reduce spacing.
    - Above age 10: Same as at 10 (full spacing), no shift.
    
    Sex factor can still be used to slightly adjust spacing if desired,
    or you can keep it at 1.0 if you don't want sex differences.
    """
    # Base spacing factor: at age 10, factor=1.0
    # We no longer reduce spacing below age 10, so factor is always 1.0.
    spacing_factor = 1.0
    
    # Frontal shift: at age < 10, introduce a negative shift (towards nasion).
    # For example, at age=1, strong shift; at age=10, no shift.
    # Let's say at age=1: shift = -0.15 (more frontal)
    # At age=10: shift = 0.0
    # We'll do a linear interpolation between age=1 and age=10:
    # age=1 -> shift=-0.15
    # age=10 -> shift=0.0
    # If age < 1, just cap it at -0.15
    # If age > 10, no shift.
    if age < 1:
        front_shift = -0.15
    elif age > 10:
        front_shift = 0.0
    else:
        # Linear interpolation between age=1 and age=10
        # (age-1)/9 moves from 0 at age=1 to 1 at age=10
        front_shift = -0.15 * (1 - (age - 1)/9.0)
        # at age=1: (age-1)/9=0 -> front_shift = -0.15
        # at age=10: (age-1)/9=1 -> front_shift = -0.15*(1-1)=0
    
    # Sex factor: if you still want a slight reduction for females, apply it here
    sex_factor = 0.95 if sex.lower() == 'female' else 1.0

    # The final factor applied to spacing remains 1.0 but we have sex_factor if needed
    final_spacing_factor = spacing_factor * sex_factor

    return final_spacing_factor, front_shift

def get_midline_fractions(age, sex):
    """
    Compute the midline fractions with the new logic:
    - At age 10: standard offsets (no shift)
    - Under age 10: same offsets, but apply a frontal shift
    - Above age 10: standard offsets
    """
    cz_fraction = 0.50
    # Standard offsets at full spacing (age 10)
    offsets = {
        'Fpz': -0.40,
        'Fz':  -0.30,
        'Pz':   0.20,
        'Oz':   0.40
    }

    spacing_factor, front_shift = get_scale_factor_for_midline(age, sex)
    
    fractions = {'Cz': cz_fraction}
    for label, offset in offsets.items():
        # Apply spacing factor (if needed) to the offset
        scaled_offset = offset * spacing_factor
        # Apply the front shift (which moves all electrodes forward for <10 years)
        # Moving forward (towards the nasion) means decreasing the fraction value 
        # along the nasion-inion axis. The front_shift is negative, pushing points forward.
        fractions[label] = cz_fraction + scaled_offset + front_shift

    return fractions, spacing_factor, front_shift

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
    midline_fracs, spacing_factor, front_shift = get_midline_fractions(age, sex)
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
st.write("This app calculates and visualizes electrode positions based on age, sex, and head dimensions.")

# Sidebar inputs for parameters
st.sidebar.header("Parameters")
age = st.sidebar.number_input("Age (years)", min_value=0.0, value=5.0, step=0.1)
sex = st.sidebar.selectbox("Sex", options=["male", "female"])
nasion_inion_distance = st.sidebar.number_input("Nasion-Inion distance (cm)", min_value=1.0, value=35.0)
preauricular_distance = st.sidebar.number_input("Preauricular distance (cm)", min_value=1.0, value=30.0)

#Compute the midline fractions with a frontal shift.
midline_fracs, spacing_factor, front_shift = get_midline_fractions(age, sex)

# Compute electrode positions with given parameters
electrodes, nasion, inion, lpa, rpa, ni_dist, pa_dist = compute_electrodes(age, sex, nasion_inion_distance, preauricular_distance)

st.subheader("Calculated Values")
st.write(f"**Final Spacing Factor:** {spacing_factor}")
st.write(f"**Frontal Shift:** {front_shift}")

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
