import streamlit as st
import matplotlib.pyplot as plt

def get_scale_factor_for_midline(age_months, sex, nasion_inion_dist):
    """
    Returns a scaling factor and a precomputed front shift in cm based on age in months and sex.
    """
    spacing_factor = 1.0  # Full spacing remains constant

    # Precomputed fractions for front shift
    if age_months <= 12:
        # Linear interpolation: 3 cm to 2 cm
        front_shift_cm = 3 - (age_months / 12) * (3 - 2)
    elif age_months <= 48:
        # Linear interpolation: 2 cm to 1 cm
        front_shift_cm = 2 - ((age_months - 12) / 36) * (2 - 1)
    elif age_months <= 120:
        # Linear interpolation: 1 cm to 0 cm
        front_shift_cm = 1 - ((age_months - 48) / 72) * 1
    else:
        # No shift for ages above 120 months
        front_shift_cm = 0.0

    # Sex factor
    sex_factor = 0.95 if sex.lower() == 'female' else 1.0

    final_spacing_factor = spacing_factor * sex_factor
    return final_spacing_factor, front_shift_cm

def get_midline_fractions(age_months, sex, nasion_inion_dist):
    """
    Compute the midline fractions with a frontal shift.
    Ensures Cz is at the true center of the nasion-inion distance.
    """
    cz_fraction = 0.50  # Cz is at the middle of the nasion-inion axis

    # Electrode offsets relative to Cz
    offsets = {
        'Fpz': -0.40,
        'Fz':  -0.30,
        'Pz':   0.20,
        'Oz':   0.40
    }

    # Calculate spacing and frontal shift
    spacing_factor, front_shift_cm = get_scale_factor_for_midline(age_months, sex, nasion_inion_dist)

    # Convert frontal shift to a fraction of nasion-inion distance
    front_shift_fraction = front_shift_cm / nasion_inion_dist

    # Apply frontal shift only for positions above Cz
    fractions = {'Cz': cz_fraction}
    for label, offset in offsets.items():
        scaled_offset = offset * spacing_factor
        # Apply shift only to electrodes in the front
        #if offset < 0:
        fractions[label] = cz_fraction + scaled_offset + front_shift_fraction
        #else:
        #    fractions[label] = cz_fraction + scaled_offset

    return fractions, spacing_factor, front_shift_cm

def plot_electrode_positions(fractions, nasion_inion_dist, preauricular_dist):
    """
    Plot the electrode positions on a head circle.
    """
    fig, ax = plt.subplots(figsize=(6, 6))

    # Compute head circle radius based on nasion-inion and preauricular distances
    head_radius = (nasion_inion_dist + preauricular_dist) / 4
    circle = plt.Circle((0, 0), head_radius, color='blue', fill=False, linestyle='--', label='Head Boundary')
    ax.add_artist(circle)

    # Plot electrodes
    for label, fraction in fractions.items():
        x = 0
        y = (fraction - 0.5) * nasion_inion_dist  # Center Cz at 0.5
        ax.plot(x, y, 'ro')
        ax.text(x, y + 0.02, label, fontsize=10, ha='center')

    ax.set_xlim(-head_radius, head_radius)
    ax.set_ylim(-head_radius, head_radius)
    ax.set_aspect('equal', 'box')
    ax.set_title("Electrode Positions")
    ax.set_xlabel("Preauricular Distance")
    ax.set_ylabel("Nasion-Inion Distance")
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)


# Streamlit UI
st.title("Electrode Positioning on Scalp")
st.write("This app calculates and visualizes electrode positions based on age (in months), sex, and head dimensions.")

# Inputs
age_months = st.slider("Age (months)", min_value=1, max_value=240, value=120, step=1)
sex = st.selectbox("Sex", ["Male", "Female"])
nasion_inion_dist = st.number_input("Nasion-Inion Distance (cm)", min_value=20.0, max_value=50.0, value=35.0, step=0.1)
preauricular_dist = st.number_input("Preauricular Distance (cm)", min_value=20.0, max_value=50.0, value=30.0, step=0.1)

# Calculations
fractions, spacing_factor, front_shift_cm = get_midline_fractions(age_months, sex, nasion_inion_dist)

# Display Results
st.write("### Calculated Values")
st.write(f"**Final Spacing Factor:** {spacing_factor}")
st.write(f"**Cz Fraction (Center):** {fractions['Cz']}")
st.write(f"**Frontal Shift (cm):** {front_shift_cm:.2f} cm")

# Plot
st.write("### Electrode Positions")
plot_electrode_positions(fractions, nasion_inion_dist, preauricular_dist)
