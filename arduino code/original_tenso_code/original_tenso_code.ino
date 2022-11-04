#include "HX711.h"                                            // подключаем библиотеку для работы с тензодатчиком

#define DT  A0                                                // Указываем номер вывода, к которому подключен вывод DT  датчика
#define SCK A1                                                // Указываем номер вывода, к которому подключен вывод SCK датчика

HX711 scale;                                                 // создаём объект scale

float calibration_factor = -14.15;                            // вводим калибровочный коэффициент
float units;                                                  // задаём переменную для измерений в граммах
float ounces;                                                 // задаём переменную для измерений в унциях

void setup() {
  Serial.begin(115200);                                         // инициируем работу последовательного порта на скорости 9600 бод
  scale.begin(DT, SCK);  // инициируем работу с датчиком
  scale.set_scale();                                          // выполняем измерение значения без калибровочного коэффициента
  scale.tare();                                               // сбрасываем значения веса на датчике в 0
  scale.set_scale(calibration_factor);                        // устанавливаем калибровочный коэффициент 
}

void loop() {                                 // выводим текст в монитор последовательного порта
  for (int i = 0; i < 1; i ++) {                             // усредняем показания, считав значения датчика 10 раз
    units = + scale.get_units(), 5;                          // суммируем показания 10 замеров
  }
  units = units;                                         // усредняем показания, разделив сумму значений на 10
  ounces = units * 0.035274 / 2.0 * 0.318669;                                  // переводим вес из унций в граммы
  Serial.println(ounces, 4);                                 // выводим текст в монитор последовательного порта
}
