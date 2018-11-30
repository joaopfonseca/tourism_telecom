/* global window,document */
import React, {Component} from 'react';
import {render} from 'react-dom';
import MuseumFountain from './components/museum-fountain.js';
import CdrFountain from './components/cdr-fountain.js';
import Header from './components/header.js';

import {json as requestJson} from 'd3-request';

// Set your mapbox token here
const MAPBOX_TOKEN = 'pk.eyJ1IjoiaWZsYW1lbnQiLCJhIjoiY2o1an' +
'VidmhnMmE2MzJ3cnl3a3Z0NXUwcCJ9.sQQjL5Nb_m-CGRnm7_y65w';

const tooltipStyle = {
  position: 'absolute',
  padding: '4px',
  background: 'rgba(0, 0, 0, 0.8)',
  color: '#fff',
  maxWidth: '300px',
  fontSize: '10px',
  zIndex: 9,
  pointerEvents: 'none'
};

const strings = {
  1: {
    showFrom: false,
    title: 'Where Do Tourists Go?',
    description: 'These are the percentages of tourists who leave to go to each of the following destinations',
    type: 'museum'
  },
  0: {
    showFrom: true,
    title: 'Where Do Tourists Come From?',
    description: 'These are the percentages of tourists who arrived to this destination from each of the following destinations',
    type: 'museum'
  },
  3: {
    showFrom: false,
    title: 'Where Do Tourists Go?',
    description: 'These are the percentages of tourists leaving this location in August 2017 as calculated from telecom data',
    type: 'daytripper'
  },
  2: {
    showFrom: true,
    title: 'Where Do Tourists Come From?',
    description: 'These are the percentages of tourists arriving to this location in August 2017 as calculated from telecom data',
    type: 'daytripper'
  }
}

class Root extends Component {

  constructor(props) {
    super(props);
    this.state = {
      selectedTab: 0,
      selectedTo: false,
      selectedStrings: 0
    };
  }

  handleTabClick(index) {
    this.setState({ 
      selectedTab: index,
      selectedStrings: (index * 2 + this.state.selectedTo)
    });
  }

  handleToFromToggle(direction) {
    this.setState({ 
      selectedTo: direction,
      selectedStrings: (this.state.selectedTab * 2 + direction)
    });
  }

  render() {
    const { selectedTab, selectedStrings } = this.state;
    const { showFrom, title, description, type } = strings[selectedStrings];
    const isMuseum = type === 'museum';
    const isDaytripper = type === 'daytripper';

    return (
      <div>
        <Header
          siteTitle="Tourism in Portugal"
          tabs={[
            { title: 'Telecom' }
          ]}
          onTabClick={this.handleTabClick.bind(this)}
          selectedTab={selectedTab}
        />

        {isMuseum && <CdrFountain
          defaultItemId="227"
          mapboxToken={MAPBOX_TOKEN}
          isOutFlow={!showFrom}
          title={title}
          description={description}
          onToggleClick={this.handleToFromToggle.bind(this)}
        />}
      </div>
    );
  }
}

render(<Root />, document.body.appendChild(document.createElement('div')));
