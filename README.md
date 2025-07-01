# gnss-solve
## Quick Start
Place gnss log files and buildings files in `.loacl` folder, as shown below.
```
.local
├── Beijing
│   ├── Beijing_Buildings_DWG-Polygon.cpg
│   ├── Beijing_Buildings_DWG-Polygon.dbf
│   ├── Beijing_Buildings_DWG-Polygon.prj
│   ├── Beijing_Buildings_DWG-Polygon.sbn
│   ├── Beijing_Buildings_DWG-Polygon.sbx
│   ├── Beijing_Buildings_DWG-Polygon.shp
│   ├── Beijing_Buildings_DWG-Polygon.shp.xml
│   └── Beijing_Buildings_DWG-Polygon.shx
├── gnss_log_1.csv
├── gnss_log_2.csv
├── gnss_log_3.csv
└── gnss_log_4.csv
```

Run `main.py` with [uv](https://docs.astral.sh/uv/).
```
uv run main.py
```
