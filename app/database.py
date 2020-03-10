import os
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import func
import geoalchemy2
from sqlalchemy import Table, MetaData
from sqlalchemy.ext.declarative import declarative_base


def get_env_variable(name):
    try:
        return os.environ[name]
    except KeyError:
        message = "Expected environment variable '{}' not set.".format(name)
        raise Exception(message)


POSTGRES_URL = get_env_variable("POSTGRES_URL")
POSTGRES_USER = get_env_variable("POSTGRES_USER")
POSTGRES_PW = get_env_variable("POSTGRES_PW")
POSTGRES_DB = get_env_variable("POSTGRES_DB")


DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(
    user=POSTGRES_USER,
    pw=POSTGRES_PW,
    url=POSTGRES_URL,
    db=POSTGRES_DB
)


PROGRESS_NUMBER_MAX = {
    'max_km_electricity': 'km electricity grid tracked',
    'max_villages': 'villages remotely mapped',
    'max_buildings': 'buildings mapped'
}
engine = create_engine(DB_URL)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))


Base = declarative_base(metadata=MetaData(schema='se4all', bind=engine))
BaseWeb = declarative_base(metadata=MetaData(schema='web', bind=engine))


class DlinesSe4all(Base):
    __table__ = Table('distribution_line_se4all', Base.metadata, autoload=True, autoload_with=engine)

class BoundaryAdmin(Base):
    __table__ = Table('boundary_adm1', Base.metadata, autoload=True, autoload_with=engine)

class AdmStatus(Base):
    __table__ = Table('boundary_adm1_status', Base.metadata, autoload=True, autoload_with=engine)


class GaugeMaximum(BaseWeb):
    __table__ = Table('ourprogress_maximums', BaseWeb.metadata, autoload=True, autoload_with=engine)


class MappedVillages(BaseWeb):
    __table__ = Table('ourprogress_villagesremotelymapped', BaseWeb.metadata, autoload=True,
                      autoload_with=engine)


class MappedBuildings(BaseWeb):
    __table__ = Table('ourprogress_buildingsmapped', BaseWeb.metadata, autoload=True,
                      autoload_with=engine)


def select_materialized_view(engine, view_name, schema=None, limit=None):
    if schema is not None:
        view_name = "{}.{}".format(schema, view_name)
    if limit is None:
        limit = ""
    else:
        limit = " LIMIT {}".format(limit)
    with engine.connect() as con:
        rs = con.execute('SELECT * FROM {}{};'.format(view_name, limit))
        data = rs.fetchall()
    return data


def query_electrified_km():
    res = select_materialized_view(engine, "ourprogress_kmelectricitygridtracked_value_v", schema="web")[0][0]
    return int(res)


def query_mapped_villages():
    res = select_materialized_view(engine, "ourprogress_villagesremotelymapped_value_v", schema="web")[0][0]
    return int(res)


def query_mapped_buildings():
    res = select_materialized_view(engine, "ourprogress_buildingsmapped_value_v", schema="web")[0][0]
    return int(res)


def query_gauge_maximum(desc):
    """Query the maximum value for a given progress gauge

    :param desc: the name of the variable under "Our progress in numbers" on the website
    :return: the maximum value as string
    """
    res = db_session.query(GaugeMaximum.maximum.label("max"))\
        .filter(GaugeMaximum.description.ilike("%{}%".format(desc))).first()
    return str(int(res.max))


def get_state_codes():
    res = db_session.query(
        BoundaryAdmin.adm1_pcode.label("code"),
        BoundaryAdmin.adm1_en.label("name")
    )
    return {r.name:r.code.lower() for r in res}


def query_available_og_clusters():
    """Look for state which have true set for both clusters and og_clusters"""
    res = db_session.query(
        AdmStatus.adm1_pcode
    ).filter(AdmStatus.cluster_all & AdmStatus.cluster_offgrid).all()
    return [r.adm1_pcode for r in res]


OG_CLUSTERS_COLUMNS = ('adm1_pcode', 'cluster_offgrid_id', 'area_km2',
    'building_count', 'percentage_building_area', 'grid_dist_km', 'geom')


def get_random_og_cluster(engine, view_code, schema="web", limit=5):
    """Select a random cluster from a given view

    :param engine: database engine
    :param view_name: the state code of the view formatted as "ngXYZ"
    :param schema: the name of the database schema
    :param limit: the number of villages to choose from
    :return: the information of one cluster : 'adm1_pcode', 'cluster_offgrid_id', 'area_km2',
    'building_count', 'percentage_building_area', 'grid_dist_km', 'geom'
    """

    if schema is not None:
        view_name = "{}.cluster_offgrid_{}_mv".format(schema, view_code)
    cols = ", ".join(OG_CLUSTERS_COLUMNS[:-1])
    cols = cols + ", ST_AsGeoJSON(ST_Centroid(ST_TRANSFORM(geom, 4326))) as geom"
    with engine.connect() as con:
        rs = con.execute('SELECT {} FROM {} ORDER BY area_km2 DESC LIMIT {};'.format(cols,
                                                                                     view_name, limit))
        data = rs.fetchall()
    single_cluster = data[random.randint(0, min([int(limit), len(data)])-1)]
    return {key: str(single_cluster[key]) for key in OG_CLUSTERS_COLUMNS}


def query_random_og_cluster(state_name, state_codes_dict):
    return get_random_og_cluster(engine=engine, view_code=state_codes_dict[state_name])



def filter_materialized_view(
        engine,
        view_name,
        schema=None,
        area=None,
        distance_grid=None,
        building=None,
        buildingfp=None,
        limit=None,
        keys=None,
):
    if schema is not None:
        view_name = "{}.{}".format(schema, view_name)
    if limit is None:
        limit = ""
    else:
        limit = " LIMIT {}".format(limit)

    filter_cond = ""

    if area is not None:
        key = "area_km2"
        filter_cond = f" WHERE {view_name}.{key} > {area[0]} AND {view_name}.{key} < {area[1]}"

    if distance_grid is not None:
        key = "grid_dist_km"
        if "WHERE" in filter_cond:
            filter_cond = filter_cond + f" AND {view_name}.{key} > {distance_grid[0]} AND" \
                                        f" {view_name}.{key} < {distance_grid[1]}"
        else:
            filter_cond = f" WHERE {view_name}.{key} > {distance_grid[0]} AND" \
                          f" {view_name}.{key} < {distance_grid[1]}"

    if building is not None:
        key = "building_count"
        if "WHERE" in filter_cond:
            filter_cond = filter_cond + f" AND {view_name}.{key} > {building[0]} AND" \
                                        f" {view_name}.{key} < {building[1]}"
        else:
            filter_cond = f" WHERE {view_name}.{key} > {building[0]} AND"\
                          f" {view_name}.{key} < {building[1]}"

    if buildingfp is not None:
        key = "percentage_building_area"
        if "WHERE" in filter_cond:
            filter_cond = filter_cond + f" AND {view_name}.{key} > {buildingfp[0]} AND" \
                                        f" {view_name}.{key} < {buildingfp[1]}"
        else:
            filter_cond = f" WHERE {view_name}.{key} > {buildingfp[0]} AND" \
                          f" {view_name}.{key} < {buildingfp[1]}"

    if keys is None:
        columns = "*"
    else:
        if not isinstance(keys, str):
            columns = ", ".join(keys)
        else:
            columns = "COUNT({})".format(keys)
    with engine.connect() as con:
        query = 'SELECT {} FROM {}{}{};'.format(columns, view_name, filter_cond, limit)
        rs = con.execute(query)
        data = rs.fetchall()
    return data


def query_filtered_clusters(
        state_name,
        state_codes_dict,
        area=None,
        distance_grid=None,
        limit=None,
        keys=None
):
    """

    :param state_name:
    :param state_codes_dict:
    :param area:
    :param distance_grid:
    :param limit:
    :param keys:
    :return:
    """
    if state_name in state_codes_dict:
        view_name = "cluster_all_{}_mv".format(state_codes_dict[state_name])
        answer = filter_materialized_view(
            engine,
            view_name,
            schema="web",
            area=area,
            distance_grid=distance_grid,
            limit=limit,
            keys=keys
        )
    else:
        print("Non existent state name: {}".format(state_name))
        answer = []
    return answer


def query_filtered_og_clusters(
        state_name,
        state_codes_dict,
        area=None,
        distance_grid=None,
        building=None,
        buildingfp=None,
        limit=None,
        keys=None
):
    """

    :param state_name:
    :param state_codes_dict:
    :param area:
    :param distance_grid:
    :param building:
    :param buildingfp:
    :param limit:
    :param keys:
    :return:
    """
    if state_name in state_codes_dict:
        view_name = "cluster_offgrid_{}_mv".format(state_codes_dict[state_name])
        answer = filter_materialized_view(
            engine,
            view_name,
            schema="web",
            area=area,
            distance_grid=distance_grid,
            building=building,
            buildingfp=buildingfp,
            limit=limit,
            keys=keys
        )
    else:
        print("Non existent state name: {}".format(state_name))
        answer = []
    return answer
