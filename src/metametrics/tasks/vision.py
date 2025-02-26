from typing import List, Dict, Any
from datasets import DatasetDict

import os
import pandas as pd
import numpy as np

from metametrics.tasks.base import MetaMetrics, MetricManager
from metametrics.optimizer import *
from metametrics.metrics import *

from metametrics.utils.logging import get_logger
from metametrics.utils.constants import TEXT_HYP, TEXT_REF, TEXT_SRC, IMG_SRC

logger = get_logger(__name__)

class MetaMetricsText(MetaMetrics):
    def __init__(self):
        self.metric_list = []
        self.optimizer = None
        self.metric_manager = MetricManager()
    
    def add_metric(self, metric_name: str, metric_args: Dict[str, Any]):
        self.metric_manager.add_metric(metric_name, metric_args)
        
    def set_optimizer(self, optimizer_name: str, optimizer_args: Dict[str, Any]):
        self.optimizer = super().get_optimizer(optimizer_name, optimizer_args)
        
    def evaluate_metrics(self, dataset, normalize_metrics):
        all_metric_scores = []
        image_sources = dataset[IMG_SRC]
        text_predictions = dataset[TEXT_HYP]
        text_references = dataset[TEXT_REF]
        text_sources = dataset[TEXT_SRC]
        
        for metric in self.metrics_manager:               
            # Get the metric scores for each metric and convert it to a list if necessary
            if isinstance(metric, BaseMetric):
                metric_scores = list(np.array(metric.run_scoring(text_predictions, text_references, text_sources)))
            elif isinstance(metric, VisionToTextBaseMetric):
                metric_scores = list(np.array(metric.run_scoring(image_sources, text_predictions,
                                                                 text_references, text_sources)))
            
            all_metric_scores.append(metric_scores)  # Append the metric scores to the list
            
        if normalize_metrics:
            all_metric_scores = self.metric_manager.normalize_all_scores(all_metric_scores)
        
        return all_metric_scores
        
    def calibrate(self, metrics_df, target_scores):
        self.optimizer.optimize(metrics_df, target_scores)
        self.need_calibrate = False
    
    def evaluate_metametrics(self, metrics_df, target_scores):
        if self.need_calibrate:
            logger.error("Modification to MetaMetrics was made, calibration is needed before evaluation!")
            raise RuntimeError()
        else:
            Y_pred = self.optimizer.predict(metrics_df)
            result = self.optimizer.evaluate(Y_pred, target_scores)
            return Y_pred, result    

