from pathlib import Path
import pandas as pd
import geopandas
from shiny import App, ui, render, reactive, Inputs, Outputs, Session
from shinywidgets import output_widget, render_widget, register_widget
from ipyleaflet import Map, basemaps, basemap_to_tiles, CircleMarker
from ipywidgets import HTML

from db_client import Client
from utils import format_string_from_list

client = Client(local_port=6000)

sp_qry = "SELECT DISTINCT scientific_name FROM specimen;"
species = client.pull_data(sp_qry)
species = list(species['scientific_name'])

fm_qry = "SELECT DISTINCT formation FROM collection_event;"
formations = client.pull_data(fm_qry)
formations = list(formations['formation'])

field_num_qry = "SELECT DISTINCT collection_id, field_number FROM collection_event;"
field_nums = client.pull_data(field_num_qry)
field_nums = dict(zip(list(field_nums['collection_id']), list(field_nums['field_number'])))
field_nums[''] = ''

locality_qry = "SELECT DISTINCT locality_id, locality_name FROM locality;"
localities = client.pull_data(locality_qry)
localities = dict(zip(list(localities['locality_id']), list(localities['locality_name'])))
localities[''] = ''

det_qry = "SELECT DISTINCT individual_id, first_name || ' ' || last_name AS \"name\" FROM individual;"
dets = client.pull_data(det_qry)
dets = dict(zip(list(dets['individual_id']), list(dets['name'])))
dets[''] = ''

basemap_choices = {
    "OpenStreetMap": basemaps.OpenStreetMap.Mapnik,
    "WorldImagery": basemaps.Esri.WorldImagery,
    "OpenTopoMap": basemaps.OpenTopoMap
}

card_filters = ui.card(
    ui.card_header("Filters", class_='my-card-header'),
    ui.input_selectize(
        id="select_species",
        label="Select species:",  
        choices=species,  
        selected = 'Hebertella occidentalis',
        multiple=True, 
        options={"plugins": ["clear_button"]}
        ), 
        ui.input_action_button("select_all_s_btn",
                               "Select all"),
        ui.input_selectize(  
            id="select_formation",  
            label="Select formations:",  
            choices=formations,  
            multiple=True, 
            options={"plugins": ["clear_button"]}
        ),
        ui.input_action_button("select_all_f_btn", "Select all"),
        ui.input_select(
            id="base_map",
            label="Select basemap:",
            choices = list(basemap_choices.keys()),
            selected='OpenStreetMap'
        ),
        full_screen=True,
)

# Card for map
card_map = ui.card(
    ui.card_header("Map", class_='my-card-header'),
    output_widget("map"),
    full_screen=True,
)

# Card for the data table
card_data = ui.card(
    ui.card_header("Data", class_='my-card-header'),
    ui.output_data_frame("pulled_data"),
    full_screen=True,
)

# Card for customizable query card
card_query_input = ui.card(
    ui.card_header("Query", class_='my-card-header'),
    ui.input_text_area('query_builder', "",
                       width="100%",
                       height=20)
)

# Card for results of query
card_query_output = ui.card(
    ui.card_header("Results", class_='my-card-header'),
    ui.output_data_frame("queried_data"),
    full_screen=True
)

card_run_query = ui.card(
    ui.input_action_button(
        'run_query',
        'Run Query', 
        class_='my_button')
)

from shiny import App, ui

app_ui = ui.page_fluid(
    ui.include_css(Path(__file__).parent / "styles.css"),
    ui.navset_card_tab(
        # Explorer Tab
        ui.nav_panel("Data Explorer",
            ui.layout_columns(
                card_filters,
                card_map,
                card_data,
                col_widths={"sm": (3, 9, 12)},
                #row_heights=(2, 3),
                height="1500px",
    ),
        ),
        # Add specimen tab
        ui.nav_panel("Add Specimen",
            ui.layout_columns(
                
            ui.input_text('phylum_text', 'Phylum'),
            ui.input_text('class_text', 'Class'),
            ui.input_text('order_text', 'Order'),
            ui.input_text('family_text', 'Family'),
            ui.input_text('genus_text', 'Genus'),
            ui.input_text('species_text', 'Scientific Name'),
            ui.input_text('common_text', 'Common Name'),
            ui.input_text('box_text', 'Box ID'),
            ui.input_text('drawer_text', 'Drawer ID'),
            ui.input_text('drawer_loc', 'Drawer Location'),
            ui.input_selectize('collection_sel', 'Collection ID',
                            choices=field_nums, multiple=False,
                            selected=''),
            ui.input_selectize('det_sel', 'Determiner',
                            choices=dets, multiple=False,
                            selected=''),
            ui.input_text('length_text', 'Length'),
            ui.input_text('width_text', 'Width'),
            ui.input_text('height_text', 'Height'),
            ui.input_text('rock_text', 'Rock Type'),
            ui.input_checkbox('mult_input', 'Multiple Individuals'),
            ui.input_text('species_array', 'Species List'),
            ui.input_text('common_array', 'Common Name List'),
            ui.input_text('age_text', 'Approximate Age'),
            ui.input_text('age_min', 'Minimum Age'),
            ui.input_text('age_max', 'Maximum Age'),
            ui.input_text_area('remark_text', 'Specimen Remarks'),
            ui.input_action_button("run_specimen_stmt", "Add Specimen", class_='my_button'),
            ui.output_text('specimen_stmt'),
            
            col_widths={"sm": 12, "lg": (4, 4, 4)}
        )
        ),

        # Add locality tab
        ui.nav_panel("Add Locality",
            ui.layout_columns(
            
            ui.input_text('locality_name', 'Locality Name'),
            ui.input_text('latitude', 'Latitude'),
            ui.input_text('longitude', 'Longitude'),
            ui.input_text('country', 'Country'),
            ui.input_text('country_code', 'Country Code'),
            ui.input_text('state_province', 'State/Province'),
            ui.input_text('state_code', 'State Code'),
            ui.input_text('county', 'County'),
            ui.input_text('municipality', 'Municipality'),
            ui.input_action_button("run_locality_stmt", "Add Locality", class_='my_button'),
            ui.output_text('locality_test'),

            col_widths={"sm": 12, "lg": (4, 4, 4)}
        )
        ),

        # Add collection event tab
        ui.nav_panel("Add Collection Event",
            ui.layout_columns(
            ui.input_selectize('loc_sel', 'Locality',
                               choices=localities, multiple=False,
                               selected=''),
            ui.input_text('field_number', 'Field Number'),
            ui.input_text('collection_date', 'Collection Date'),
            ui.input_text('specific_latitude', 'Specific Latitude'),
            ui.input_text('specific_longitude', 'Specific Longitude'),
            ui.input_text('elevation', 'Elevation'),
            ui.input_text('stage', 'Stage'),
            ui.input_text('formation', 'Formation'),
            ui.input_text('formation_code', 'Formation Code'),
            ui.input_text('specific_formation', 'Specific Formation'),
            ui.input_text('participants', 'Participants'),
            ui.input_selectize('collector_sel', 'Collector',
                            choices=dets, multiple=False,
                            selected=''),
            ui.input_text_area('collection_remarks', 'Collection Remarks'),
            ui.input_action_button("run_collection_stmt", "Add Collection Event", class_='my_button'),

            ui.output_text('collection_stmt'),

            col_widths={"sm": 12, "lg": (4, 4, 4)}
        )
        ),

        ui.nav_panel("Custom Query",
                     ui.layout_columns(
                        card_query_input,
                        card_run_query,
                        card_query_output,
                        col_widths={"sm": (10, 2, 12)},
                        height="800px",
                     ))
    )
)

def server(input: Inputs, output: Outputs, session: Session):

    # Reactive to pull data from database 
    @reactive.calc
    def pull_data():

        species_str = format_string_from_list(input.select_species())
        formations_str = format_string_from_list(input.select_formation())

        species_check = species_str == ''
        formations_check = formations_str == ''
        
        if species_check and formations_check:
            cols = ['scientific_name', 'locality_name', 'latitude', 
                    'longitude', 'formation', 'formation_code',
                    'length', 'width', 'height', 'phylum',
                    'class', 'order', 'family', 'rock_type',
                    'collection_date', 'collector', 'collection_remarks',
                    'specimen_remarks']
            return pd.DataFrame({}, columns=cols)
        
        else:

            qry = """
            SELECT 
                s.scientific_name,
                l.locality_name,
                ce.specific_latitude as latitude,
                ce.specific_longitude as longitude,
                ce.formation,
                ce.formation_code,
                s.length,
                s.width,
                s.height,
                s.phylum,
                s.class,
                s.order,
                s.family,
                s.rock_type,
                ce.collection_date,
                i.first_name || i.last_name as collector,
                ce.collection_remarks,
                s.specimen_remarks
            FROM specimen as s 
            LEFT JOIN collection_event as ce on ce.collection_id = s.collection_id
            LEFT JOIN locality as l on l.locality_id = ce.locality_id
            LEFT JOIN individual as i on i.individual_id = ce.collector_id
            WHERE 1=1
            """ 
                    
            if species_str != '':
                qry += f' AND s.scientific_name IN ({species_str})'
            if formations_str != '':
                qry += f' AND ce.formation IN ({formations_str})'

            df = client.pull_data(qry)
            return df
    
    # Render dataframe of pulled data
    @render.data_frame
    def pulled_data():
        return render.DataGrid(pull_data())
    
    # Button to add all species
    @reactive.effect
    @reactive.event(input.select_all_s_btn)
    def _():
        ui.update_selectize("select_species", selected=species)

    # Button to add all formations
    @reactive.effect
    @reactive.event(input.select_all_f_btn)
    def _():
        ui.update_selectize("select_formation", selected=formations)
        
    # Map
    @render_widget
    def map():

        # Set basemap
        selected_basemap = input.base_map()
        basemap = basemap_to_tiles(basemap_choices[selected_basemap])
        
        center = [39.296, -84.405]
        zoom = 10

        m = Map(center=center, zoom=zoom)
        m.add_layer(basemap)

        color_map = {
            'Porifera': '#FFC33B',
            'Conulariida': '#009F81',
            'Cnidaria': '#FF5AAF',
            'Arthropoda': '#00FCCF', 
            'Mollusca': '#8400CD',
            'Bryozoa': '#008DF9', 
            'Brachiopoda': '#00C2F9',
            'Echinodermata': '#FFB2FD',
            'Conodonta': '#A40122',
            'Hemichordata': '#E20134',
            'Chordata': '#FF6E3A',
            'Other': '#888888',
        }

        df = pull_data()
        df = df.dropna(subset='latitude').reset_index(drop=True)
        df['color'] = df.phylum.apply(lambda x: color_map[x])
        
        for index, row in df.iterrows():
            marker = CircleMarker(
                location=(row['latitude'], row['longitude']),
                radius=10,
                weight=1,
                color='black',
                fill_color=row['color'],
                fill_opacity=0.8,
            )

            popup_html = HTML(f"<b>Species:</b> {row['scientific_name']} <br> <b>Date</b> {row['collection_date']}")
            marker.popup = popup_html

            m.add_layer(marker)
        return m
    
    @reactive.calc
    def make_specimen_stmt():
        """Function to create Insert statement for adding new specimen"""

        stmt = "INSERT INTO specimen ("
        values = "VALUES ("

        if input.phylum_text() != '':
            stmt = stmt + "phylum, "
            values = values + f"'{input.phylum_text()}', "

        if input.class_text() != '':
            stmt = stmt + '"class", '
            values = values + f"'{input.class_text()}', "

        if input.order_text() != '':
            stmt = stmt + '"order", '
            values = values + f"'{input.order_text()}', "

        if input.family_text() != '':
            stmt = stmt + '"family", '
            values = values + f"'{input.family_text()}', "

        if input.genus_text() != '':
            stmt = stmt + "genus, "
            values = values + f"'{input.genus_text()}', "

        if input.species_text() != '':
            stmt = stmt + "scientific_name, "
            values = values + f"'{input.species_text()}', "

        if input.common_text() != '':
            stmt = stmt + "common_name, "
            values = values + f"'{input.common_text()}', "

        if input.box_text() != '':
            stmt = stmt + "box_id, "
            values = values + f"'{input.box_text()}', "
        
        if input.drawer_text() != '':
            stmt = stmt + "drawer_id, "
            values = values + f"'{input.drawer_text()}', "

        if input.drawer_loc() != '':
            stmt = stmt + "drawer_loc, "
            values = values + f"'{input.drawer_loc()}', "

        if input.collection_sel() != '':
            stmt = stmt + "collection_id, "
            values = values + f"'{input.collection_sel()}', "

        if input.det_sel() != '':
            stmt = stmt + "determiner_id, "
            values = values + f"'{input.det_sel()}', "

        if input.length_text() != '':
            stmt = stmt + "length, "
            values = values + f"{input.length_text()}, "

        if input.width_text() != '':
            stmt = stmt + "width, "
            values = values + f"{input.width_text()}, "

        if input.height_text() != '':
            stmt = stmt + "height, "
            values = values + f"{input.height_text()}, "

        if input.rock_text() != '':
            stmt = stmt + "rock_type, "
            values = values + f"'{input.rock_text()}', "

        if input.mult_input():
            stmt = stmt + "multiple_individuals, "
            values = values + "TRUE, "
        else:
            stmt = stmt + "multiple_individuals, "
            values = values + "FALSE, "

        if input.species_array() != '':
            stmt = stmt + "scientific_name_array, "
            values = values + f"'{input.species_array()}', "

        if input.common_array() != '':
            stmt = stmt + "common_name_array, "
            values = values + f"'{input.common_array()}', "

        if input.age_text() != '':
            stmt = stmt + "approximate_age "
            values = values + f"'{input.age_text()}', "

        if input.age_min() != '':
            stmt = stmt + "min_age, "
            values = values + f"{input.age_min()}, "

        if input.age_max() != '':
            stmt = stmt + "max_age, "
            values = values + f"{input.age_max()}, "

        if input.remark_text() != '':
            stmt = stmt + "specimen_remarks, "
            values = values + f"'{input.remark_text()}', "

        stmt = stmt.strip(', ') + ')'
        values = values.strip(', ') + ')'
        return stmt + ' ' + values + ';'
    
    @reactive.calc
    def make_locality_stmt():
        """Function to create Insert statement for adding new locality"""

        stmt = "INSERT INTO locality ("
        values = "VALUES ("

        if input.locality_name() != '':
            stmt = stmt + "locality_name, "
            values = values + f"'{input.locality_name()}', "

        if input.latitude() != '':
            stmt = stmt + "latitude, "
            values = values + f"{input.latitude()}, "

        if input.longitude() != '':
            stmt = stmt + "longitude, "
            values = values + f"{input.longitude()}, "
        
        if input.country() != '':
            stmt = stmt + "country, "
            values = values + f"'{input.country()}', "

        if input.country_code() != '':
            stmt = stmt + "country_code, "
            values = values + f"'{input.country_code()}', "
        
        if input.state_province() != '':
            stmt = stmt + "state_province, "
            values = values + f"'{input.state_province()}', "

        if input.state_code() != '':
            stmt = stmt + "state_code, "
            values = values + f"'{input.state_code()}', "

        if input.county() != '':
            stmt = stmt + "county, "
            values = values + f"'{input.county()}', "
        
        if input.municipality() != '':
            stmt = stmt + "municipality, "
            values = values + f"'{input.municipality()}', "
        
        stmt = stmt.strip(', ') + ')'
        values = values.strip(', ') + ')'
        return stmt + ' ' + values + ';'
    
    @reactive.calc
    def make_collection_stmt():
        """Function to create Insert statement for adding new specimen"""

        stmt = "INSERT INTO collection_event ("
        values = "VALUES ("

        if input.loc_sel() != '':
            stmt = stmt + "locality_id, "
            values = values + f"'{input.loc_sel()}', "

        if input.field_number() != '':
            stmt = stmt + "field_number, "
            values = values + f"'{input.field_number()}', "

        if input.collection_date() != '':
            stmt = stmt + "collection_date, "
            values = values + f"'{input.collection_date()}', "

        if input.specific_latitude() != '':
            stmt = stmt + "specific_latitude, "
            values = values + f"{input.specific_latitude()}, "

        if input.specific_longitude() != '':
            stmt = stmt + "specific_longitude, "
            values = values + f"{input.specific_longitude()}, "

        if input.elevation() != '':
            stmt = stmt + "elevation, "
            values = values + f"{input.elevation()}, "

        if input.stage() != '':
            stmt = stmt + "stage, "
            values = values + f"'{input.stage()}', "

        if input.formation() != '':
            stmt = stmt + "formation, "
            values = values + f"'{input.formation()}', "
        
        if input.formation_code() != '':
            stmt = stmt + "formation_code, "
            values = values + f"'{input.formation_code()}', "

        if input.specific_formation() != '':
            stmt = stmt + "specific_formation, "
            values = values + f"'{input.specific_formation()}', "

        if input.participants() != '':
            stmt = stmt + "participants, "
            values = values + f"'{input.participants()}', "

        if input.collector_sel() != '':
            stmt = stmt + "collector_id, "
            values = values + f"'{input.collector_sel()}', "

        if input.collection_remarks() != '':
            stmt = stmt + "collection_remarks, "
            values = values + f"'{input.collection_remarks()}', "

        stmt = stmt.strip(', ') + ')'
        values = values.strip(', ') + ')'
        return stmt + ' ' + values + ';' 
    

    @render.text  
    def specimen_stmt():
        return make_specimen_stmt()
    
    @render.text
    def locality_test():
        return make_locality_stmt()
    
    @render.text
    def collection_stmt():
        return make_collection_stmt()
    
    # Add specimen
    @reactive.effect
    @reactive.event(input.run_specimen_stmt)
    def _():
        qry = make_specimen_stmt()
        rslt = client.run_statement(qry)

        # Update species choices
        sp_qry = "SELECT DISTINCT scientific_name FROM specimen;"
        species = client.pull_data(sp_qry)
        species = list(species['scientific_name'])

        ui.update_selectize(
            'select_species',
            choices=species
        )
        m = ui.modal(
            rslt,
            title="Query Result",
            easy_close=True,
            footer=None,
        )
        ui.modal_show(m)

    # Add locality
    @reactive.effect
    @reactive.event(input.run_locality_stmt)
    def _():
        qry = make_locality_stmt()
        rslt = client.run_statement(qry)

        # Update locality choices
        locality_qry = "SELECT DISTINCT locality_id, locality_name FROM locality;"
        localities = client.pull_data(locality_qry)
        localities = dict(zip(list(localities['locality_id']), list(localities['locality_name'])))
        localities[''] = ''

        ui.update_selectize(
            'loc_sel',
            choices=localities
        )

        m = ui.modal(
            rslt,
            title="Query Result",
            easy_close=True,
            footer=None,
        )
        ui.modal_show(m)


    # Add collection event
    @reactive.effect
    @reactive.event(input.run_collection_stmt)
    def _():
        qry = make_collection_stmt()
        rslt = client.run_statement(qry)

        # Update choices for field numbers
        field_num_qry = "SELECT DISTINCT collection_id, field_number FROM collection_event;"
        field_nums = client.pull_data(field_num_qry)
        field_nums = dict(zip(list(field_nums['collection_id']), list(field_nums['field_number'])))
        field_nums[''] = '' 

        ui.update_selectize(
            'collection_sel',
            choices=field_nums
        )

        # Update formation choices
        fm_qry = "SELECT DISTINCT formation FROM collection_event;"
        formations = client.pull_data(fm_qry)
        formations = list(formations['formation'])

        ui.update_selectize(
            'select_formation',
            choices=formations
        )

        m = ui.modal(
            rslt,
            title="Query Result",
            easy_close=True,
            footer=None,
        )
        ui.modal_show(m)


    # Run Custom Query
    @reactive.calc
    def custom_query():
        qry = input.query_builder()
        df = client.run_statement(qry, return_df=True)
        return df
    
    # Render dataframe of pulled data
    @render.data_frame
    @reactive.event(input.run_query)
    def queried_data():
        return render.DataGrid(custom_query())

app = App(app_ui, server)

