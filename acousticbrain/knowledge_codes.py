class GlobalDomainCode:
    RT60 = "RT60"
    ETC = "ETC"
    CLARITY = "CLARITY"
    SPATIAL = "SPATIAL"


class SourceAnalysisCode:
    RT60 = "RT60Analysis"
    ETC = "ETCAnalysis"
    CLARITY = "ClarityAnalysis"
    SPATIAL = "SpatialAnalysis"
    CLARITY_CORRELATION = "ClarityCorrelationAnalysis"
    SPATIAL_CORRELATION = "SpatialCorrelationAnalysis"
    ETC_REFLECTION_CORRELATION = "ETCReflectionCorrelationAnalysis"


class GlobalCorrelationCode:
    ETC_SPATIAL_ASYMMETRY = "ETC_SPATIAL_ASYMMETRY"
    RT60_CLARITY_DECAY_INTERACTION = "RT60_CLARITY_DECAY_INTERACTION"
    ETC_CLARITY_EARLY_ENERGY_INTERACTION = (
        "ETC_CLARITY_EARLY_ENERGY_INTERACTION"
    )
    SPATIAL_STEREO_ALIGNMENT = "SPATIAL_STEREO_ALIGNMENT"


class RecommendationCode:
    CHECK_EARLY_REFLECTION_SYMMETRY = "CHECK_EARLY_REFLECTION_SYMMETRY"
    INVESTIGATE_RT60_CHANNEL_DIFFERENCES = (
        "INVESTIGATE_RT60_CHANNEL_DIFFERENCES"
    )
    TREAT_DOMINANT_EARLY_REFLECTIONS = "TREAT_DOMINANT_EARLY_REFLECTIONS"
    VERIFY_TIME_ALIGNMENT = "VERIFY_TIME_ALIGNMENT"


class FactCode:
    RT60_INTERCHANNEL_HOMOGENEITY = "rt60.interchannel_homogeneity"
    RT60_RELIABLE_DIFFERENCE_COUNT = "rt60.reliable_difference_count"
    ETC_COMMON_EVENT_COUNT = "etc.common_event_count"
    ETC_CHANNEL_SPECIFIC_EVENT_COUNT = "etc.channel_specific_event_count"
    ETC_REFLECTION_DOMINANT_UNMATCHED_EVENT_COUNT = (
        "etc_reflection.dominant_unmatched_event_count"
    )
    CLARITY_CHANNEL_ASYMMETRY_COUNT = "clarity.channel_asymmetry_count"
    CLARITY_CORRELATION_COUNT = "clarity.correlation_count"
    SPATIAL_TECHNICAL_CENTER_STABILITY = (
        "spatial.technical_center_stability"
    )
    SPATIAL_CORRELATION_COUNT = "spatial.correlation_count"
