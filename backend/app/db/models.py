from sqlalchemy import (
    Column, String, Boolean, Float, Integer,
    BigInteger, Text, TIMESTAMP, Date, ForeignKey
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.database import Base


class Line(Base):
    __tablename__ = "lines"

    line_id   = Column(String, primary_key=True)
    line_name = Column(String, nullable=False)
    mode      = Column(String, nullable=False)
    operator  = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)


class Station(Base):
    __tablename__ = "stations"

    stop_id   = Column(String, primary_key=True)
    stop_name = Column(String, nullable=False)
    lat       = Column(Float)
    lon       = Column(Float)
    zone_id   = Column(String)
    # geom géré directement en SQL via PostGIS


class ScheduledPassage(Base):
    __tablename__ = "scheduled_passages"

    scheduled_id   = Column(BigInteger, primary_key=True, autoincrement=True)
    line_id        = Column(String, ForeignKey("lines.line_id"), nullable=False)
    stop_id        = Column(String, ForeignKey("stations.stop_id"), nullable=False)
    direction      = Column(String)
    trip_id        = Column(String)
    scheduled_time = Column(TIMESTAMP, nullable=False)
    service_date   = Column(Date, nullable=False)


class ObservedPassage(Base):
    __tablename__ = "observed_passages"

    observed_id   = Column(BigInteger, primary_key=True, autoincrement=True)
    line_id       = Column(String, ForeignKey("lines.line_id"), nullable=False)
    stop_id       = Column(String, ForeignKey("stations.stop_id"), nullable=False)
    direction     = Column(String)
    observed_time = Column(TIMESTAMP, nullable=False)
    collected_at  = Column(TIMESTAMP, server_default=func.now())
    source_ref    = Column(String)
    status        = Column(String)
    raw_payload   = Column(JSONB)


class OfficialIncident(Base):
    __tablename__ = "official_incidents"

    incident_id    = Column(String, primary_key=True)
    line_id        = Column(String, ForeignKey("lines.line_id"))
    stop_id        = Column(String, ForeignKey("stations.stop_id"))
    severity       = Column(String)
    start_time     = Column(TIMESTAMP, nullable=False)
    end_time       = Column(TIMESTAMP)
    label          = Column(String)
    description    = Column(Text)
    source_payload = Column(JSONB)


class NetworkMetric(Base):
    __tablename__ = "network_metrics"

    metric_id         = Column(BigInteger, primary_key=True, autoincrement=True)
    computed_at       = Column(TIMESTAMP, server_default=func.now())
    line_id           = Column(String, ForeignKey("lines.line_id"), nullable=False)
    stop_id           = Column(String, ForeignKey("stations.stop_id"))
    window_size_min   = Column(Integer, default=5)
    mean_delay        = Column(Float)
    abs_mean_delay    = Column(Float)
    punctuality_score = Column(Float)
    regularity_score  = Column(Float)
    missing_passages  = Column(Integer, default=0)
    headway_gap       = Column(Float)
    anomaly_score     = Column(Float)
    network_state     = Column(String)


class Event(Base):
    __tablename__ = "events"

    event_id               = Column(BigInteger, primary_key=True, autoincrement=True)
    computed_at            = Column(TIMESTAMP, server_default=func.now())
    line_id                = Column(String, ForeignKey("lines.line_id"), nullable=False)
    stop_id                = Column(String, ForeignKey("stations.stop_id"))
    event_type             = Column(String, nullable=False)
    severity               = Column(String, nullable=False)
    anomaly_score          = Column(Float)
    network_state          = Column(String)
    status                 = Column(String, default="ouvert")
    official_incident_flag = Column(Boolean, default=False)
    description            = Column(Text)


class EventQualification(Base):
    __tablename__ = "event_qualifications"

    qualification_id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_id         = Column(BigInteger, ForeignKey("events.event_id"), nullable=False)
    agent_id         = Column(String, nullable=False)
    qualification    = Column(String, nullable=False)
    comment          = Column(Text)
    qualified_at     = Column(TIMESTAMP, server_default=func.now())
