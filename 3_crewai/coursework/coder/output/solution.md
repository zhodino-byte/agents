```python
def calculate_recall(true_positives, false_negatives):
    """
    Calculate recall
    :param true_positives: Number of true positive cases
    :param false_negatives: Number of false negative cases
    :return: Recall value
    """
    if (true_positives + false_negatives) == 0:
        return 0.0
    recall = true_positives / (true_positives + false_negatives)
    return recall

# Example usage
if __name__ == '__main__':
    tp = 70  # True Positives
    fn = 30  # False Negatives
    recall_value = calculate_recall(tp, fn)
    print(f'Recall: {recall_value:.2f}')
```
Recall: 0.70