# -- coding: utf-8 --
# @Time    : 2024/2/12 21:28
# @Author  : TangKai
# @Team    : ZheChengData

"""
路网点层信息存储与相关方法
"""

import pandas as pd
import geopandas as gpd
from ..GlobalVal import NetField
from shapely.geometry import Point


net_field = NetField()
node_id_field = net_field.NODE_ID_FIELD
geometry_field = net_field.GEOMETRY_FIELD


class Node(object):
    def __init__(self, node_gdf: gpd.GeoDataFrame = None, geo_crs: str = 'EPSG:4326', plane_crs: str = 'EPSG:32650',
                 is_check: bool = True):
        self.geo_crs = geo_crs
        self.plane_crs = plane_crs
        self.__node_gdf = node_gdf.copy()
        self.max_node_id = None
        self.__available_node_id = None
        if is_check:
            self.check()
        self.init_available_node_id()

    def check(self):
        gap_set = {node_id_field, geometry_field} - set(self.__node_gdf.columns)
        assert len(gap_set) == 0, rf'线层Link缺少以下字段:{gap_set}'
        assert len(self.__node_gdf[node_id_field]) == len(self.__node_gdf[node_id_field].unique()), \
            rf'字段{node_id_field}不唯一...'
        for col in [node_id_field]:
            assert len(self.__node_gdf[self.__node_gdf[col].isna()]) == 0, rf'点层Node字段{col}有空值...'
            self.__node_gdf[col] = self.__node_gdf[col].astype(int)
        assert self.__node_gdf.crs == self.geo_crs, rf'源文件Node:地理坐标系指定有误:实际:{self.__node_gdf.crs}, 指定: {self.geo_crs}'

    def init_node(self):
        self.__node_gdf.set_index(node_id_field, inplace=True)
        self.__node_gdf[node_id_field] = self.__node_gdf.index

    def get_node_geo(self, node_id: int = None):
        return self.__node_gdf.at[node_id, geometry_field]

    def get_node_loc(self, node_id: int = None) -> tuple:
        geo = self.get_node_geo(node_id)
        return geo.x, geo.y

    def get_node_data(self) -> gpd.GeoDataFrame:
        return self.__node_gdf.copy()

    def modify_node_gdf(self, node_id_list: list[int], attr_field_list:list[str], val_list: list[list] = None):
        self.__node_gdf.loc[node_id_list, attr_field_list] = val_list

    @property
    def crs(self):
        return self.__node_gdf.crs

    def to_plane_prj(self) -> None:
        if self.__node_gdf.crs == self.plane_crs:
            pass
        else:
            self.__node_gdf = self.__node_gdf.to_crs(self.plane_crs)

    def to_geo_prj(self) -> None:
        if self.__node_gdf.crs == self.geo_crs:
            pass
        else:
            self.__node_gdf = self.__node_gdf.to_crs(self.geo_crs)

    def init_available_node_id(self) -> None:
        max_node = self.__node_gdf[node_id_field].max()
        self.max_node_id = max_node
        self.__available_node_id = list({i for i in range(1, max_node + 1)} - set(self.__node_gdf[node_id_field]))

    @property
    def available_node_id(self) -> int:
        if self.__available_node_id:
            now_node_id = self.__available_node_id.pop()
            return now_node_id
        else:
            self.init_available_node_id()
            if self.__available_node_id:
                now_node_id = self.__available_node_id.pop()
                return now_node_id
            else:
                now_node_id = self.max_node_id
                self.max_node_id += 1
                return now_node_id + 1

    def append_nodes(self, node_id: list[int], geo: list[Point], **kwargs):
        attr_dict = {node_id_field: node_id, geometry_field: geo}
        attr_dict.update(kwargs)
        _new = gpd.GeoDataFrame(attr_dict, geometry=geometry_field, crs=self.__node_gdf.crs)
        _new.index = _new[node_id_field]
        self.__node_gdf = pd.concat(
            [self.__node_gdf, _new])

    def delete_nodes(self, node_list: list[int]) -> gpd.GeoDataFrame:
        del_node_gdf = self.__node_gdf.loc[node_list, :].copy()
        self.__node_gdf.drop(index=node_list, inplace=True, axis=0)
        return del_node_gdf

    def update_available_node_id(self, node_list: list[int], _type: str = 'new'):
        if _type == 'new':
            self.__available_node_id = list(set(self.__available_node_id) - set(node_list))
        elif _type == 'del':
            self.__available_node_id.extend(node_list)
            self.__available_node_id = list(set(self.__available_node_id))
        else:
            raise ValueError('_type para: only del or new is allowed!')