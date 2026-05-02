from dataclasses import dataclass

@dataclass
class RawLead:
    """Minimal representation of a candidate from LinkedIn search results."""
    name: str
    title: str
    profile_url: str


@dataclass
class Profile:
    """Detailed information extracted from a LinkedIn profile."""
    name: str
    title: str
    company: str
    location: str
    profile_url: str


@dataclass
class EnrichedLead:
    """Profile augmented with email and domain for lead generation."""
    name: str
    role: str
    company: str
    email: str
    domain: str
    location: str
    profile_url: str
