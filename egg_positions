import streamlit as st
import matplotlib.pyplot as plt

def interpolate_point(p1, p2, fraction):
    """Linearly interpolate between p1 and p2 by a fraction (0 to 1)."""
    return (p1[0] + fraction * (p2[0] - p1[0]),
            p1[1] + fraction * (p2[1] - p1[1]))

def get_scale_factor_for_midline(age, sex):
    """
    Returns a factor by which we scale the midline offsets from Cz.
    Hypothetical model:
    - Base factor = 1.0 for adult male.
    - At age 1, factor = 0.7 (70%), linearly approaching 1.0 by age 20.
    - For female, reduce by an additional 5%.
    """
    # Age scaling
    if age < 1:
        age_factor = 0.7
    elif age > 20:
        age_factor = 1.0
    else:
        # linear interpolation: at age=1, factor=0.7; at age=20, factor=1.0
        age_factor = 0.7 + (1.0 - 0.7) * ((age - 1) / (20 - 1))

    # Sex scaling
    if sex.lower() == 'female':
        sex_factor = 0.95
    else:
        sex_factor = 1.0

    return age_factor * sex_factor

def get_midline_fractions(age, sex):
    """
    Compute midline fractions based on age and sex.
    We keep Cz fixed at 0.50. Other points are offsets from Cz:
      Fpz: Cz - 0.40
      Fz:  Cz - 0.30
      Pz:  Cz + 0.20
      Oz:  Cz + 0.40
    Scale these offsets by a factor depending on age and sex.
    """
    cz_fraction = 0.50
    offsets = {
        'Fpz': -0.40,
        'Fz':  -0.30,
        'Pz':  0.20,
        'Oz':  0.40
    }

    scale = get_scale_factor_for_midline(age, sex)

    fractions = {'Cz': cz_fraction}
    for label, offset in offsets.items():
        fractions[label] = cz_fraction + offset * scale

    return fractions

def compute_electrodes(age, sex, nasion_inion_distance, preauricular_distance):
    nasion = (0.0, 0.0)
    inion = (0.0, -nasion_inion_distance)

    # For simplicity, place preauricular points halfway down
    mid_vertical = nasion_inion_distance * 0.5
    left_preauricular = (-preauricular_distance/2.0, -mid_vertical)
    right_preauricular = (preauricular_distance/2.0, -mid_vertical)

    # Get midline fractions based on age and sex
    midline_fracs = get_midline_fractions(age, sex)

    electrodes = {}
    for label, frac in midline_fracs.items():
        electrodes[label] = interpolate_point(nasion, inion, frac)

    def place_lateral_electrodes(midline_label, left_label, right_label):
        mid_x, mid_y = electrodes[midline_label]
        total_height = nasion_inion_distance
        rel_y = (mid_y - inion[1]) / total_height
        
        left_bound = interpolate_point(inion, left_preauricular, rel_y)
        right_bound = interpolate_point(inion, right_preauricular, rel_y)
        
        # For simplicity, we keep the 0.3 fraction for lateral placement
        left_elec_pos = interpolate_point((mid_x, mid_y), left_bound, 0.3)
        right_elec_pos = interpolate_point((mid_x, mid_y), right_bound, 0.3)
        
        electrodes[left_label] = left_elec_pos
        electrodes[right_label] = right_elec_pos

    # Place lateral electrodes
    place_lateral_electrodes('Fpz', 'Fp1', 'Fp2')
    place_lateral_electrodes('Fz', 'F3', 'F4')
    place_lateral_electrodes('Cz', 'C3', 'C4')
    place_lateral_electrodes('Pz', 'P3', 'P4')
    place_lateral_electrodes('Oz', 'O1', 'O2')

    def place_temporal_electrodes(y_label, left_label, right_label, fraction_from_mid=0.8):
        mid_x, mid_y = electrodes[y_label]
        total_height = nasion_inion_distance
        rel_y = (mid_y - inion[1]) / total_height
        left_bound = interpolate_point(inion, left_preauricular, rel_y)
        right_bound = interpolate_point(inion, right_preauricular, rel_y)
        left_pos = interpolate_point((mid_x, mid_y), left_bound, fraction_from_mid)
        right_pos = interpolate_point((mid_x, mid_y), right_bound, fraction_from_mid)
        electrodes[left_label] = left_pos
        electrodes[right_label] = right_pos

    # Place temporal electrodes
    place_temporal_electrodes('Cz', 'T7', 'T8')

    return electrodes, nasion, inion, left_preauricular, right_preauricular, nasion_inion_distance


# Streamlit UI
st.title("EEG Electrode Placement (2D)")

st.sidebar.header("Parameters")
age = st.sidebar.number_input("Age (years)", min_value=0.0, value=5.0, step=1.0)
sex = st.sidebar.selectbox("Sex", options=["male", "female"])
nasion_inion_distance = st.sidebar.number_input("Nasion-Inion distance (cm)", min_value=1.0, value=35.0)
preauricular_distance = st.sidebar.number_input("Preauricular distance (cm)", min_value=1.0, value=30.0)

electrodes, nasion, inion, lpa, rpa, ni_dist = compute_electrodes(age, sex, nasion_inion_distance, preauricular_distance)

# Display electrode coordinates
st.subheader("Electrode Coordinates")
for name, coord in electrodes.items():
    st.write(f"{name}: {coord}")

# Plot the head and electrodes
radius = ni_dist / 2.0
fig, ax = plt.subplots(figsize=(6,6))

# Draw the head as a circle
head_circle = plt.Circle((0, -radius), radius, color='lightblue', alpha=0.3)
ax.add_artist(head_circle)

# Plot electrodes
for name, (x,y) in electrodes.items():
    ax.scatter(x, y, c='r')
    ax.text(x, y, name, fontsize=9, ha='center', va='bottom', color='black')

# Plot reference points
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

st.pyplot(fig)
