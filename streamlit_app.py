import streamlit as st
import re

# Page config
st.set_page_config(
    page_title="STL Tags Converter",
    layout="wide"
)

# Mapping from old tag names/types to new theme_prop names
TAG_MAPPING = {
    'CMResultsAdUrl_font-size': 'ad_url_font_size',
    'CMResultsAdUrl_color': 'ad_url_font_color',
    'CMResultsAdUrl_font-family': 'ad_url_font_family',  # Fixed: hyphen -> underscore
    'CMResultsAdTitle_font-size': 'ad_title_font_size',
    'CMResultsAdTitle_color': 'ad_title_color',
    'CMResultsAdTitle_font-family': 'ad_title_font_family',
    'CMResultsAdDescription_font-size': 'ad_desc_font_size',
    'CMResultsAdDescription_color': 'ad_desc_font_color',
    'CMResultsAdDescription_font-family': 'ad_desc_font_family',
    'ResultsAdDescription_font-size': 'ad_desc_desktop_font_size',
    'CustomResultsAdUrlBackGround_color': 'ad_background',
    'CustomResultsAdUrlBorder_color': 'ad_border_color',
    'CMContentArea_color': 'body_background',
    'HeaderArea_color': 'header_background',
    'AdBorder_color': 'cta_border_color',
    'CMAdsLabel_color': 'cta_background',
    'Bullet_font-size': 'cta_text_font_size',
    'BulletText_color': 'cta_text_font_color',
    'BulletShape_color': 'chevron_color',
    'KeywordsHoverUnderline_checkbox': 'title_hover_underline',
    'KeywordArea_color': 'keyword_link_color',
    'relcontspan_font-family': 'relcont_span_font_family',
    'HeaderText_font-size': 'header_text_font_size',
    'HeaderText_color': 'header_text_color',
    'HeaderText_textCase': 'header_text_case',
    'HeaderText_tallness': 'header_border_width',
    'HeaderText_border-style': 'header_border_style',
    'CMResultsAdUrl_font-size_desktop': 'ad_url_desktop_font_size',
    'CMResultsAdTitle_font-size_desktop': 'ad_title_desktop_font_size',
    'AdBorder_color_desktop': 'cta_border_desktop_color',
    'InnerBorder_color': 'ad_url_font_color',
    'CallToAction_content': 'cta_text'
}

def convert_tag(match, name, value, type):
    """Convert old tag format to new theme_prop format"""
    key = f"{name}_{type}"
    new_prop_name = TAG_MAPPING.get(key)
    
    # If no mapping found, create a default name
    if not new_prop_name:
        # Convert CamelCase to snake_case
        new_prop_name = re.sub(r'([A-Z])', r'_\1', name).lower().lstrip('_').replace('__', '_') + '_' + type.lower()
    
    return f'<tag:theme_prop:{new_prop_name} default="{value}" />'

def get_context_suffix(context_before, css_property=None):
    """Get context suffix based on surrounding code"""
    suffix = ""
    
    # Check if inside media query (desktop)
    if '@media' in context_before:
        # Find the last @media before this tag
        media_pos = context_before.rfind('@media')
        if media_pos != -1:
            # Check if there's a closing brace after @media (meaning we're still inside)
            after_media = context_before[media_pos:]
            open_braces = after_media.count('{')
            close_braces = after_media.count('}')
            if open_braces > close_braces:
                suffix = "_desktop"
                return suffix  # Desktop takes priority
    
    # Check CSS property context
    if css_property:
        css_prop_lower = css_property.lower()
        if 'border' in css_prop_lower and 'color' in css_prop_lower:
            suffix = "_border"
            return suffix  # Border color takes priority
    
    # Check selector context (more specific selectors first)
    selector_match = re.search(r'\.([a-z-]+)\s*\{[^}]*$', context_before)
    if selector_match:
        selector = selector_match.group(1)
        if 'arrow-text' in selector:
            suffix = "_cta_text"
        elif 'arrow' in selector or 'cta' in selector:
            suffix = "_cta"
        elif 'title' in selector and 'arrow' not in selector:
            suffix = "_title"
    
    return suffix

def find_duplicate_props(output):
    """Find all prop names that appear more than once"""
    prop_pattern = r'<tag:theme_prop:([^>\s]+)\s+default=["\']([^"\']*)["\']\s*/>'
    matches = list(re.finditer(prop_pattern, output))
    
    # Group by prop name
    prop_groups = {}
    for match in matches:
        prop_name = match.group(1)
        if prop_name not in prop_groups:
            prop_groups[prop_name] = []
        prop_groups[prop_name].append({
            'match': match,
            'value': match.group(2),
            'position': match.start(),
            'full_match': match.group(0)
        })
    
    # Return only duplicates (appears more than once)
    duplicates = {name: occurrences for name, occurrences in prop_groups.items() 
                 if len(occurrences) > 1}
    
    return duplicates

def rename_duplicates(output, original_html):
    """Rename duplicate prop names with context suffixes"""
    duplicates = find_duplicate_props(output)
    
    if not duplicates:
        return output
    
    # Find all original tags in order
    original_tags = []
    for match in re.finditer(r'<tagd:style\s+name=["\']([^"\']+)["\']\s+value=["\']([^"\']*)["\']\s+type=["\']([^"\']+)["\']\s*/>', original_html, re.IGNORECASE):
        original_tags.append({
            'match': match,
            'name': match.group(1),
            'value': match.group(2),
            'type': match.group(3),
            'position': match.start()
        })
    for match in re.finditer(r'<tagd:style\s+type=["\']([^"\']+)["\']\s+name=["\']([^"\']+)["\']\s+value=["\']([^"\']*)["\']\s*/>', original_html, re.IGNORECASE):
        original_tags.append({
            'match': match,
            'name': match.group(2),
            'value': match.group(3),
            'type': match.group(1),
            'position': match.start()
        })
    original_tags.sort(key=lambda x: x['position'])
    
    # Find all converted tags in order
    converted_tags = []
    for match in re.finditer(r'<tag:theme_prop:([^>\s]+)\s+default=["\']([^"\']*)["\']\s*/>', output):
        converted_tags.append({
            'match': match,
            'prop_name': match.group(1),
            'value': match.group(2),
            'position': match.start()
        })
    converted_tags.sort(key=lambda x: x['position'])
    
    # Match converted tags to original tags by position order
    # Process duplicates in reverse order to maintain positions
    all_replacements = []
    for prop_name, occurrences in duplicates.items():
        # Keep first occurrence, rename others
        for i, occ in enumerate(occurrences):
            if i == 0:
                continue  # Keep first one
            
            # Find this occurrence in converted_tags list
            occ_index = None
            for idx, conv_tag in enumerate(converted_tags):
                if conv_tag['position'] == occ['position']:
                    occ_index = idx
                    break
            
            if occ_index is not None and occ_index < len(original_tags):
                # Get corresponding original tag
                orig_tag = original_tags[occ_index]
                context_start = max(0, orig_tag['position'] - 1000)
                context_before = original_html[context_start:orig_tag['position']]
            else:
                # Fallback: use converted output context
                context_start = max(0, occ['position'] - 1000)
                context_before = output[context_start:occ['position']]
            
            # Extract CSS property from original HTML
            css_prop_match = re.search(r'([a-z-]+):\s*<tagd:style', context_before[-300:], re.IGNORECASE)
            css_property = css_prop_match.group(1) if css_prop_match else None
            
            # Get context suffix
            suffix = get_context_suffix(context_before, css_property)
            
            # If no suffix found, use index as fallback
            if not suffix:
                suffix = f"_{i}"
            
            # Create new prop name
            new_prop_name = prop_name + suffix
            
            # Replace this occurrence
            old_tag = occ['full_match']
            new_tag = old_tag.replace(f'<tag:theme_prop:{prop_name}', f'<tag:theme_prop:{new_prop_name}')
            all_replacements.append((occ['position'], old_tag, new_tag))
    
    # Sort by position (reverse order) and replace
    all_replacements.sort(key=lambda x: x[0], reverse=True)
    for position, old_tag, new_tag in all_replacements:
        output = output[:position] + new_tag + output[position + len(old_tag):]
    
    return output

def convert_tags(input_html):
    """Main conversion function with two-pass approach"""
    if not input_html or not input_html.strip():
        return ""
    
    original_html = input_html  # Keep original for context detection
    output = input_html
    
    # PASS 1: Convert <tagd:style name="..." value="..." type="..." /> to <tag:theme_prop:... default="..." />
    output = re.sub(
        r'<tagd:style\s+name=["\']([^"\']+)["\']\s+value=["\']([^"\']*)["\']\s+type=["\']([^"\']+)["\']\s*/>',
        lambda m: convert_tag(m.group(0), m.group(1), m.group(2), m.group(3)),
        output,
        flags=re.IGNORECASE
    )
    
    # Also handle tags with different attribute order
    output = re.sub(
        r'<tagd:style\s+type=["\']([^"\']+)["\']\s+name=["\']([^"\']+)["\']\s+value=["\']([^"\']*)["\']\s*/>',
        lambda m: convert_tag(m.group(0), m.group(2), m.group(3), m.group(1)),
        output,
        flags=re.IGNORECASE
    )
    
    # PASS 2: Find and rename duplicates with context suffixes
    output = rename_duplicates(output, original_html)
    
    # Clean up: ensure tags don't have excessive line breaks around them
    output = re.sub(r'\s*\n\s*(<tag:[^>]+>)\s*\n\s*', r' \1 ', output)
    output = re.sub(r'(<tag:[^>]+>)\s*\n\s*', r'\1 ', output)
    
    return output

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def text_contrast_color(hex_color):
    """Return black or white text based on hex color luminance"""
    try:
        r, g, b = hex_to_rgb(hex_color)
        luminance = (0.299*r + 0.587*g + 0.114*b) / 255
        return "black" if luminance > 0.6 else "white"
    except:
        return "black"

def is_color_value(value):
    """Check if value is a color (hex, rgb, etc.)"""
    if not value:
        return False
    
    value = str(value).strip()
    
    if not value:
        return False
    
    # Hex color: #fff, #ffffff, etc.
    if re.match(r'^#[0-9a-fA-F]{3,6}$', value):
        return True
    
    # RGB/RGBA: rgb(255,255,255), rgba(255,255,255,1)
    if re.match(r'^rgba?\(', value, re.IGNORECASE):
        return True
    
    # Named colors (basic check)
    named_colors = ['red', 'blue', 'green', 'white', 'black', 'transparent', 
                   'yellow', 'orange', 'purple', 'pink', 'gray', 'grey',
                   'cyan', 'magenta', 'lime', 'navy', 'maroon', 'olive',
                   'teal', 'silver', 'gold', 'brown', 'tan', 'beige']
    if value.lower() in named_colors:
        return True
    
    return False

def extract_theme_props(html_content):
    """Extract all theme_prop tags and their values"""
    pattern = r'<tag:theme_prop:([^>\s]+)\s+default=["\']([^"\']*)["\']\s*/>'
    matches = re.findall(pattern, html_content)
    
    props = []
    seen = set()
    for prop_name, default_value in matches:
        # Avoid duplicates in the list
        key = (prop_name, default_value)
        if key not in seen:
            seen.add(key)
            props.append({
                'Property Name': prop_name,
                'Default Value': default_value,
                'Is Color': is_color_value(default_value)
            })
    
    return props

def get_text_color_for_bg(bg_color):
    """Determine text color (black or white) based on background color brightness"""
    if not bg_color:
        return "#000000"
    
    bg_color = bg_color.strip()
    
    # Handle hex colors
    if bg_color.startswith('#'):
        hex_color = bg_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # Calculate brightness using relative luminance formula
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            
            # Use white text for dark backgrounds, black for light
            return "#ffffff" if brightness < 128 else "#000000"
        except:
            return "#000000"
    
    # Handle RGB/RGBA colors
    rgb_match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', bg_color)
    if rgb_match:
        try:
            r = int(rgb_match.group(1))
            g = int(rgb_match.group(2))
            b = int(rgb_match.group(3))
            
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            return "#ffffff" if brightness < 128 else "#000000"
        except:
            return "#000000"
    
    # For named colors, use black text by default (most named colors are light)
    return "#000000"

def style_dataframe(df):
    """Apply color highlighting to Default Value column"""
    def style_cell(val):
        if is_color_value(str(val)):
            text_color = text_contrast_color(str(val))
            return f"background-color: {val}; color: {text_color}"
        return ""
    
    return df.style.applymap(style_cell, subset=['Default Value'])

def replace_theme_props_with_values(html_content):
    """Replace theme_prop tags with their default values"""
    if not html_content or not html_content.strip():
        return ""
    
    output = html_content
    
    # Replace <tag:theme_prop:... default="..." /> with just the value
    pattern = r'<tag:theme_prop:[^>\s]+\s+default=["\']([^"\']*)["\']\s*/>'
    output = re.sub(pattern, r'\1', output)
    
    return output

def replace_stl_content_tags_with_samples(html_content):
    """Replace STL content tags with sample text for rendering, based on sample source code pattern"""
    if not html_content or not html_content.strip():
        return ""
    
    output = html_content
    
    # Remove conditional tags but keep their content (if:ad_present1)
    output = re.sub(r'<if:([^>]+)>', '', output)
    output = re.sub(r'</if:([^>]+)>', '', output)
    
    # Replace tag:ad_annotation_enabled1 with number for class (annot1)
    # Pattern: class="annot<tag:ad_annotation_enabled1 />" becomes class="annot1"
    output = re.sub(r'<tag:ad_annotation_enabled(\d+)\s*/>', r'\1', output)
    
    # Replace customtag:adClickUrl1 with span element
    output = re.sub(r'<customtag:adClickUrl(\d+)\s+data-type="([^"]+)"\s*/>', r'<span class="adClickUrl\1" data-type="\2" ></span>', output)
    
    # Replace tagd:style with type="content" - extract the value
    output = re.sub(r'<tagd:style\s+name="[^"]+"\s+value="([^"]+)"\s+type="content"\s*/>', r'\1', output)
    
    # Remove empty/script tags
    output = re.sub(r'<tag:post_form_html\s*/>', '', output)
    output = re.sub(r'<tag:jssource\s*/>', '', output)
    
    # Replace meta/title tags with sample values
    output = re.sub(r'<tag:page_title\s*/>', 'Sample Page Title', output)
    output = re.sub(r'<tag:charset\s*/>', 'UTF-8', output)
    
    # Replace ad content tags with sample text (more realistic samples)
    output = re.sub(r'<tag:ad_sldtld(\d+)\s*/>', r'example.com', output)
    output = re.sub(r'<ad_title_text:(\d+)\s*/>', r'Sample Ad Title \1', output)
    output = re.sub(r'<ad_desc:(\d+)\s*/>', r'This is a sample ad description for ad \1. It provides details about the product or service being advertised.', output)
    output = re.sub(r'<ad_href_url:(\d+)\s*/>', r'#', output)
    
    # Replace web/article content tags with sample text
    output = re.sub(r'<web_title_text:(\d+)\s*/>', r'Sample Article Title \1', output)
    output = re.sub(r'<web_desc:(\d+)\s*/>', r'This is a sample article description \1. It provides a brief summary of the article content.', output)
    output = re.sub(r'<web_href_url:(\d+)\s*/>', r'#', output)
    
    # Footer links - leave empty (as shown in sample source code)
    output = re.sub(r'<footer_links\s*/>', '', output)
    
    return output

def display_properties_table(props):
    """Display properties table"""
    if not props:
        st.info("No theme properties found in the input.")
        return
    
    # Sort props: colors first, then non-colors
    sorted_props = sorted(props, key=lambda x: (not x['Is Color'], x['Property Name']))
    
    # Create simple table data
    table_data = []
    for prop in sorted_props:
        table_data.append({
            'Property Name': prop['Property Name'],
            'Default Value': prop['Default Value']
        })
    
    # Display styled table
    import pandas as pd
    df = pd.DataFrame(table_data)
    st.dataframe(style_dataframe(df), use_container_width=True, hide_index=True)
    
    # Create CSV format for copying
    csv_lines = ["key,value"]
    for prop in props:
        csv_lines.append(f"{prop['Property Name']},{prop['Default Value']}")
    csv_content = "\n".join(csv_lines)
    
    # Show CSV button
    show_csv = st.button("Show CSV", key="show_csv", use_container_width=True)
    if show_csv:
        st.code(csv_content, language=None)

# Custom CSS to reduce top padding
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# UI
st.title("Theme Smith Tools")
st.markdown("---")

# Create tabs
tab1, tab2 = st.tabs(["Modify Framework", "Theme Editor"])

with tab1:
    st.subheader("Modify standard FW to Theme Smith FW")
    
    # Create two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Standard FW**")
        
        input_text = st.text_area(
            "Paste your old framework HTML here:",
            value="",
            height=600,
            key="input",
            label_visibility="collapsed"
        )
        
        # Convert button
        st.button("Convert", key="convert", use_container_width=True)
    
    with col2:
        st.markdown("**Theme Smith FW**")
        
        # Always convert when there's input
        output_text = ""
        if input_text and input_text.strip():
            output_text = convert_tags(input_text)
        
        # Display output textarea - use dynamic key based on input hash to force updates
        input_hash = hash(input_text) if input_text else 0
        st.text_area(
            "Converted HTML:",
            value=output_text,
            height=600,
            key=f"output_{input_hash}",
            label_visibility="collapsed",
            placeholder="Converted HTML will appear here..."
        )

with tab2:
    st.subheader("Theme Editor & Preview")
    
    st.markdown("Paste your New Framework HTML to edit theme properties and see live preview.")
    
    # Input for new framework HTML
    editor_input = st.text_area(
        "Paste New Framework HTML:",
        value="",
        height=200,
        key="editor_input",
        placeholder="Paste HTML containing <tag:theme_prop:... default=\"...\" /> tags here..."
    )
    
    # Button to load and extract properties
    load_button = st.button("Load Theme Properties", use_container_width=True)
    
    if load_button and editor_input and editor_input.strip():
        # Extract theme properties
        props = extract_theme_props(editor_input)
        
        if props:
            # Store in session state
            st.session_state.editor_html = editor_input
            st.session_state.editor_props = props
            
            # Automatically generate preview with default values
            st.session_state.modified_html = editor_input
            preview_html = replace_theme_props_with_values(editor_input)
            preview_html = replace_stl_content_tags_with_samples(preview_html)
            st.session_state.preview_html = preview_html
            
            st.success(f"Loaded {len(props)} theme properties and generated preview!")
    
    # Show editor if properties are loaded
    if 'editor_props' in st.session_state and st.session_state.editor_props:
        st.markdown("---")
        
        # Create two columns
        col1_editor, col2_editor = st.columns(2)
        
        with col1_editor:
            # Heading with Apply Changes button inline
            col_heading, col_button = st.columns([3, 1])
            with col_heading:
                st.markdown("**Edit Theme Properties:**")
            with col_button:
                apply_button = st.button("Apply Changes", use_container_width=True)
            
            # Create editable dataframe
            import pandas as pd
            
            # Prepare data for editable table - sort colors to top
            props_list = st.session_state.editor_props
            
            # Sort: colors first, then others
            sorted_props = sorted(props_list, key=lambda x: (not x['Is Color'], x['Property Name']))
            
            table_data = []
            for prop in sorted_props:
                table_data.append({
                    'Property': prop['Property Name'],
                    'Value': prop['Default Value'],
                    '_is_color': prop['Is Color']  # Hidden column for color preview
                })
            
            df = pd.DataFrame(table_data)
            
            # Editable dataframe with only 2 visible columns
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                hide_index=True,
                height=600,
                column_config={
                    "Property": st.column_config.TextColumn(
                        "Property Name",
                        width="medium",
                        disabled=True
                    ),
                    "Value": st.column_config.TextColumn(
                        "Value",
                        width="medium"
                    ),
                    "_is_color": None  # Hide this column
                }
            )
            
            # Store edited values in session state
            st.session_state.edited_values = {}
            for _, row in edited_df.iterrows():
                st.session_state.edited_values[row['Property']] = row['Value']
            
            # Color preview section below the table
            st.markdown("---")
            st.markdown("**Color Preview:**")
            
            # Get color properties from edited dataframe
            color_rows = edited_df[edited_df['_is_color'] == True]
            
            if not color_rows.empty:
                # Display color swatches in columns
                cols_per_row = 4
                color_list = [(row['Property'], row['Value']) for _, row in color_rows.iterrows()]
                
                for i in range(0, len(color_list), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, col in enumerate(cols):
                        if i + j < len(color_list):
                            prop_name, color_val = color_list[i + j]
                            
                            with col:
                                # Create HTML color swatch
                                text_color = get_text_color_for_bg(color_val) if is_color_value(color_val) else "#000000"
                                color_swatch = f"""
                                <div style="
                                    background-color: {color_val};
                                    color: {text_color};
                                    padding: 8px;
                                    border-radius: 4px;
                                    text-align: center;
                                    font-size: 11px;
                                    margin-bottom: 5px;
                                    border: 1px solid #444;
                                ">
                                    {prop_name[:20]}{'...' if len(prop_name) > 20 else ''}
                                </div>
                                """
                                st.markdown(color_swatch, unsafe_allow_html=True)
            
            # CSV Download button at the bottom
            st.markdown("---")
            
            # Create CSV for download
            csv_lines = ["key,value"]
            for prop in sorted_props:
                csv_lines.append(f"{prop['Property Name']},{prop['Default Value']}")
            csv_content = "\n".join(csv_lines)
            
            st.download_button(
                label="Download CSV",
                data=csv_content,
                file_name="theme_properties.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            if apply_button:
                # Replace theme_prop tags with edited values in the HTML
                modified_html = st.session_state.editor_html
                
                for prop_name, new_value in st.session_state.edited_values.items():
                    # Replace the specific theme_prop tag with the new value
                    pattern = f'<tag:theme_prop:{re.escape(prop_name)}\\s+default=["\'][^"\']*["\']\\s*/>'
                    replacement = f'<tag:theme_prop:{prop_name} default="{new_value}" />'
                    modified_html = re.sub(pattern, replacement, modified_html)
                
                # Store modified HTML
                st.session_state.modified_html = modified_html
                
                # Generate preview by replacing theme_prop tags with values
                preview_html = replace_theme_props_with_values(modified_html)
                preview_html = replace_stl_content_tags_with_samples(preview_html)
                st.session_state.preview_html = preview_html
        
        with col2_editor:
            st.markdown("**Live Preview:**")
            
            # Show preview if available
            if 'preview_html' in st.session_state and st.session_state.preview_html:
                # Preview
                st.components.v1.html(st.session_state.preview_html, height=800, scrolling=True)
                
                # Download and copy buttons below the preview
                st.markdown("---")
                col1_btn, col2_btn, col3_btn = st.columns(3)
                with col1_btn:
                    st.download_button(
                        label="Download Modified Framework",
                        data=st.session_state.modified_html,
                        file_name="modified_framework.html",
                        mime="text/html",
                        use_container_width=True
                    )
                with col2_btn:
                    st.download_button(
                        label="Download Preview",
                        data=st.session_state.preview_html,
                        file_name="preview.html",
                        mime="text/html",
                        use_container_width=True
                    )
                with col3_btn:
                    # Copy button using expander
                    with st.expander("📋 Copy Code"):
                        st.code(st.session_state.preview_html, language="html")
            else:
                st.info("Load theme properties on the left to see the preview here.")

