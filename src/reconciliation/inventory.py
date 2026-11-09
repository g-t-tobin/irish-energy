"""
Historical data inventory service for Irish Energy Analytics Data Platform
"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from dateutil.parser import parse
from loguru import logger
from src.reconciliation.models import HistoricalDatasetInfo, DataLayer, DatasetInventory
from src.quality.models import QualityReport


class HistoricalDataInventoryService:
    """
    Service for inspecting and representing historical data inventory
    """

    def __init__(self):
        # This would normally connect to S3 or other storage
        # For now, we'll use mock data for demonstration
        self.mock_datasets = self._initialize_mock_datasets()

    def _initialize_mock_datasets(self) -> Dict[str, Dict[str, Any]]:
        """Initialize mock datasets for testing purposes"""
        return {
            'eirgrid_demand': {
                'bronze': {
                    'available_partitions': ['2023-01-01', '2023-01-02', '2023-01-04', '2023-01-05'],
                    'missing_partitions': ['2023-01-03'],
                    'record_counts': {
                        '2023-01-01': 1000,
                        '2023-01-02': 1200,
                        '2023-01-04': 1100,
                        '2023-01-05': 1300
                    },
                    'file_counts': {
                        '2023-01-01': 2,
                        '2023-01-02': 2,
                        '2023-01-04': 2,
                        '2023-01-05': 2
                    },
                    'total_file_sizes': {
                        '2023-01-01': 1024000,
                        '2023-01-02': 1228800,
                        '2023-01-04': 1126400,
                        '2023-01-05': 1331200
                    },
                    'schema_info': {
                        'fields': ['date', 'total_demand', 'avg_demand', 'min_demand', 'max_demand'],
                        'types': ['date', 'float', 'float', 'float', 'float']
                    }
                },
                'silver': {
                    'available_partitions': ['2023-01-01', '2023-01-02', '2023-01-04', '2023-01-05'],
                    'missing_partitions': [],
                    'record_counts': {
                        '2023-01-01': 1000,
                        '2023-01-02': 1200,
                        '2023-01-04': 1100,
                        '2023-01-05': 1300
                    },
                    'file_counts': {
                        '2023-01-01': 1,
                        '2023-01-02': 1,
                        '2023-01-04': 1,
                        '2023-01-05': 1
                    },
                    'total_file_sizes': {
                        '2023-01-01': 512000,
                        '2023-01-02': 614400,
                        '2023-01-04': 563200,
                        '2023-01-05': 665600
                    },
                    'schema_info': {
                        'fields': ['date', 'total_demand', 'avg_demand', 'min_demand', 'max_demand'],
                        'types': ['date', 'float', 'float', 'float', 'float']
                    }
                },
                'gold': {
                    'available_partitions': ['2023-01-01', '2023-01-02', '2023-01-04', '2023-01-05'],
                    'missing_partitions': [],
                    'record_counts': {
                        '2023-01-01': 1000,
                        '2023-01-02': 1200,
                        '2023-01-04': 1100,
                        '2023-01-05': 1300
                    },
                    'file_counts': {
                        '2023-01-01': 1,
                        '2023-01-02': 1,
                        '2023-01-04': 1,
                        '2023-01-05': 1
                    },
                    'total_file_sizes': {
                        '2023-01-01': 256000,
                        '2023-01-02': 307200,
                        '2023-01-04': 281600,
                        '2023-01-05': 332800
                    },
                    'schema_info': {
                        'fields': ['date', 'total_demand', 'avg_demand', 'min_demand', 'max_demand', 'aggregation_period'],
                        'types': ['date', 'float', 'float', 'float', 'float', 'string']
                    }
                }
            },
            'eirgrid_generation': {
                'bronze': {
                    'available_partitions': ['2023-01-01', '2023-01-02', '2023-01-04', '2023-01-05'],
                    'missing_partitions': ['2023-01-03'],
                    'record_counts': {
                        '2023-01-01': 800,
                        '2023-01-02': 900,
                        '2023-01-04': 850,
                        '2023-01-05': 950
                    },
                    'file_counts': {
                        '2023-01-01': 2,
                        '2023-01-02': 2,
                        '2023-01-04': 2,
                        '2023-01-05': 2
                    },
                    'total_file_sizes': {
                        '2023-01-01': 819200,
                        '2023-01-02': 921600,
                        '2023-01-04': 870400,
                        '2023-01-05': 972800
                    },
                    'schema_info': {
                        'fields': ['date', 'total_generation', 'avg_generation', 'min_generation', 'max_generation'],
                        'types': ['date', 'float', 'float', 'float', 'float']
                    }
                },
                'silver': {
                    'available_partitions': ['2023-01-01', '2023-01-02', '2023-01-04', '2023-01-05'],
                    'missing_partitions': [],
                    'record_counts': {
                        '2023-01-01': 800,
                        '2023-01-02': 900,
                        '2023-01-04': 850,
                        '2023-01-05': 950
                    },
                    'file_counts': {
                        '2023-01-01': 1,
                        '2023-01-02': 1,
                        '2023-01-04': 1,
                        '2023-01-05': 1
                    },
                    'total_file_sizes': {
                        '2023-01-01': 409600,
                        '2023-01-02': 460800,
                        '2023-01-04': 435200,
                        '2023-01-05': 486400
                    },
                    'schema_info': {
                        'fields': ['date', 'total_generation', 'avg_generation', 'min_generation', 'max_generation'],
                        'types': ['date', 'float', 'float', 'float', 'float']
                    }
                },
                'gold': {
                    'available_partitions': ['2023-01-01', '2023-01-02', '2023-01-04', '2023-01-05'],
                    'missing_partitions': [],
                    'record_counts': {
                        '2023-01-01': 800,
                        '2023-01-02': 900,
                        '2023-01-04': 850,
                        '2023-01-05': 950
                    },
                    'file_counts': {
                        '2023-01-01': 1,
                        '2023-01-02': 1,
                        '2023-01-04': 1,
                        '2023-01-05': 1
                    },
                    'total_file_sizes': {
                        '2023-01-01': 204800,
                        '2023-01-02': 230400,
                        '2023-01-04': 217600,
                        '2023-01-05': 243200
                    },
                    'schema_info': {
                        'fields': ['date', 'total_generation', 'avg_generation', 'min_generation', 'max_generation', 'aggregation_period'],
                        'types': ['date', 'float', 'float', 'float', 'float', 'string']
                    }
                }
            },
            'openmeteo_weather': {
                'bronze': {
                    'available_partitions': ['2023-01-01', '2023-01-02', '2023-01-04', '2023-01-05'],
                    'missing_partitions': ['2023-01-03'],
                    'record_counts': {
                        '2023-01-01': 1440,
                        '2023-01-02': 1440,
                        '2023-01-04': 1440,
                        '2023-01-05': 1440
                    },
                    'file_counts': {
                        '2023-01-01': 1,
                        '2023-01-02': 1,
                        '2023-01-04': 1,
                        '2023-01-05': 1
                    },
                    'total_file_sizes': {
                        '2023-01-01': 7372800,
                        '2023-01-02': 7372800,
                        '2023-01-04': 7372800,
                        '2023-01-05': 7372800
                    },
                    'schema_info': {
                        'fields': ['date', 'temperature', 'humidity', 'pressure', 'wind_speed'],
                        'types': ['date', 'float', 'float', 'float', 'float']
                    }
                },
                'silver': {
                    'available_partitions': ['2023-01-01', '2023-01-02', '2023-01-04', '2023-01-05'],
                    'missing_partitions': [],
                    'record_counts': {
                        '2023-01-01': 1440,
                        '2023-01-02': 1440,
                        '2023-01-04': 1440,
                        '2023-01-05': 1440
                    },
                    'file_counts': {
                        '2023-01-01': 1,
                        '2023-01-02': 1,
                        '2023-01-04': 1,
                        '2023-01-05': 1
                    },
                    'total_file_sizes': {
                        '2023-01-01': 3686400,
                        '2023-01-02': 3686400,
                        '2023-01-04': 3686400,
                        '2023-01-05': 3686400
                    },
                    'schema_info': {
                        'fields': ['date', 'avg_temperature', 'avg_humidity', 'avg_pressure', 'avg_wind_speed'],
                        'types': ['date', 'float', 'float', 'float', 'float']
                    }
                },
                'gold': {
                    'available_partitions': ['2023-01-01', '2023-01-02', '2023-01-04', '2023-01-05'],
                    'missing_partitions': [],
                    'record_counts': {
                        '2023-01-01': 1440,
                        '2023-01-02': 1440,
                        '2023-01-04': 1440,
                        '2023-01-05': 1440
                    },
                    'file_counts': {
                        '2023-01-01': 1,
                        '2023-01-02': 1,
                        '2023-01-04': 1,
                        '2023-01-05': 1
                    },
                    'total_file_sizes': {
                        '2023-01-01': 1843200,
                        '2023-01-02': 1843200,
                        '2023-01-04': 1843200,
                        '2023-01-05': 1843200
                    },
                    'schema_info': {
                        'fields': ['date', 'avg_temperature', 'avg_humidity', 'avg_pressure', 'avg_wind_speed', 'aggregation_period'],
                        'types': ['date', 'float', 'float', 'float', 'float', 'string']
                    }
                }
            }
        }

    def get_dataset_inventory(self, dataset_name: str, data_layer: DataLayer) -> Optional[HistoricalDatasetInfo]:
        """
        Get inventory information for a specific dataset

        Args:
            dataset_name: Name of the dataset
            data_layer: Data layer (bronze, silver, gold)

        Returns:
            HistoricalDatasetInfo or None if not found
        """
        try:
            dataset_info = self.mock_datasets.get(dataset_name, {}).get(data_layer.value)
            if not dataset_info:
                return None

            # Convert date strings to datetime objects for earliest/latest
            available_dates = [parse(date_str) for date_str in dataset_info['available_partitions']]
            earliest_date = min(available_dates) if available_dates else None
            latest_date = max(available_dates) if available_dates else None

            return HistoricalDatasetInfo(
                dataset_name=dataset_name,
                data_layer=data_layer,
                earliest_available_date=earliest_date,
                latest_available_date=latest_date,
                available_partitions=dataset_info['available_partitions'],
                missing_partitions=dataset_info['missing_partitions'],
                record_counts=dataset_info['record_counts'],
                file_counts=dataset_info['file_counts'],
                total_file_sizes=dataset_info['total_file_sizes'],
                schema_info=dataset_info['schema_info']
            )
        except Exception as e:
            logger.error(f"Error getting dataset inventory for {dataset_name}: {str(e)}")
            return None

    def get_all_datasets_inventory(self, data_layer: DataLayer) -> List[HistoricalDatasetInfo]:
        """
        Get inventory information for all datasets at a specific layer

        Args:
            data_layer: Data layer (bronze, silver, gold)

        Returns:
            List of HistoricalDatasetInfo objects
        """
        datasets = []
        for dataset_name in self.mock_datasets.keys():
            dataset_info = self.get_dataset_inventory(dataset_name, data_layer)
            if dataset_info:
                datasets.append(dataset_info)
        return datasets

    def get_dataset_summary(self, dataset_name: str, data_layer: DataLayer) -> Optional[DatasetInventory]:
        """
        Get a summary of dataset inventory in dictionary format

        Args:
            dataset_name: Name of the dataset
            data_layer: Data layer (bronze, silver, gold)

        Returns:
            DatasetInventory dictionary or None if not found
        """
        dataset_info = self.get_dataset_inventory(dataset_name, data_layer)
        if not dataset_info:
            return None

        return {
            'dataset_name': dataset_info.dataset_name,
            'data_layer': dataset_info.data_layer.value,
            'earliest_available_date': dataset_info.earliest_available_date.isoformat() if dataset_info.earliest_available_date else None,
            'latest_available_date': dataset_info.latest_available_date.isoformat() if dataset_info.latest_available_date else None,
            'available_partitions': dataset_info.available_partitions,
            'missing_partitions': dataset_info.missing_partitions,
            'record_counts': dataset_info.record_counts,
            'file_counts': dataset_info.file_counts,
            'total_file_sizes': dataset_info.total_file_sizes,
            'schema_info': dataset_info.schema_info
        }

    def get_all_datasets_summary(self, data_layer: DataLayer) -> List[DatasetInventory]:
        """
        Get summaries for all datasets at a specific layer

        Args:
            data_layer: Data layer (bronze, silver, gold)

        Returns:
            List of DatasetInventory dictionaries
        """
        return [self.get_dataset_summary(name, data_layer) for name in self.mock_datasets.keys()]