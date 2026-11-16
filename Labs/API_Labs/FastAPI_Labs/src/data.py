from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split


def load_data():
    """
    Load the Iris dataset.
    Returns:
        X (numpy.ndarray): Features (sepal length/width, petal length/width, in cm).
        y (numpy.ndarray): Target class ids (0, 1, 2).
        feature_names (list[str]): Feature names in column order.
        class_names (list[str]): Species name for each class id.
    """
    iris = load_iris()
    feature_names = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
    return iris.data, iris.target, feature_names, list(iris.target_names)


def split_data(X, y):
    """
    Split the data into training and testing sets.
    Stratified, so all three species appear in the same proportions in both sets.
    Returns:
        X_train, X_test, y_train, y_test (tuple): The split dataset.
    """
    return train_test_split(X, y, test_size=0.3, random_state=12, stratify=y)
