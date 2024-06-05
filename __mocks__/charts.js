// __mocks__/chart.js
const Chart = jest.fn().mockImplementation((context, config) => {
  console.log('Chart constructor called');
  return {
    data: config.data,
    options: config.options,
    resize: jest.fn(),
    update: jest.fn(),
  };
});

module.exports = {
  Chart,
};
