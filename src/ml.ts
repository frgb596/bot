import * as tf from '@tensorflow/tfjs-node';
import * as path from 'path';

class MLService {
  private minesModel: tf.LayersModel | null = null;
  private slideModel: tf.LayersModel | null = null;

  async loadModels() {
    this.minesModel = await tf.loadLayersModel(path.resolve(process.env.MINES_MODEL_PATH!));
    this.slideModel = await tf.loadLayersModel(path.resolve(process.env.SLIDE_MODEL_PATH!));
    console.log('✅ ML models loaded');
  }

  predictMines(features: number[]): number[] {
    if (!this.minesModel) throw new Error('Model not loaded');
    const tensor = tf.tensor2d([features], [1, features.length]);
    const prediction = this.minesModel.predict(tensor) as tf.Tensor;
    return prediction.arraySync()[0] as number[];
  }

  predictSlide(features: number[]): number[] {
    if (!this.slideModel) throw new Error('Model not loaded');
    const tensor = tf.tensor2d([features], [1, features.length]);
    const prediction = this.slideModel.predict(tensor) as tf.Tensor;
    return prediction.arraySync()[0] as number[];
  }
}

export const mlService = new MLService();
