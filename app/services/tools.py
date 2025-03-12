"""
Defines "application_forms" tool for AI to retrieve application form for partner colleges
"""

# Fallback url for applications
DEFAULT_APPLICATION_URL = "https://lauruseducation.com.au/study-with-us"

APPLICATION_FORM_MAP = {
    "allied": "https://forms.zohopublic.com/lauruseducation/form/AlliedStudentApplicationForm/formperma/NPbbkYR6OL2i4CY2fWpjP3UvN3PrRA5ZYy8xhiaoWwY",
    "paragon": "https://forms.zohopublic.com/lauruseducation/form/ParagonPolytechnicStudentApplicationForm/formperma/llCP88loK2iAIPPFqdiimc_4uAtXpWMCumlo6o7T5e4",
    "hilton": "https://forms.zohopublic.com/lauruseducation/form/StudentApplicationForm/formperma/Lww_pqqBlFD_H8s8oXlAubdrDRx7tG6fmFt0b5_G4do",
    "collins": "https://forms.zohopublic.com/lauruseducation/form/CollinsAcademyStudentApplicationForm/formperma/7fuuJNbDaxAcSvTwSRCRGDiMDmV-EoB-ZNiDm1wUbm8",
    "future": "https://forms.zohopublic.com/lauruseducation/form/FutureEnglishApplicationForm/formperma/LWRyxNtlvibpP6Z15Qn8c4ffGw9TlhrThrBl8N4S1aQ",
    # NOTE: Evertought has multiple enrolment forms. We will direct the students to the general enrolment url
    "everthought": "https://lauruseducation.com.au/study-with-us"
}


def application_form_tool(
    college: str # affiliated college
):
    if college == "everthought":
        return f"Everthought college has multiple enrolment forms. Direct the user to go to the url '''{DEFAULT_APPLICATION_URL}''' where they can find the enrolment form they need"""

    if college in APPLICATION_FORM_MAP:
        return f"The enrolment form can be found at '''{APPLICATION_FORM_MAP[college]}'''"

    return f"Direct the student to '''{DEFAULT_APPLICATION_URL}''' where they can find the enrolment form they need"