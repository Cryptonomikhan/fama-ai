#!/usr/bin/env python3
"""
Dashboard Tools for Fama AI.

This module provides tools for generating Next.js dashboard components
that can be used by the Dashboard Builder Agent in the Fama AI platform.
"""
import json
import logging
import os
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# Base tool class
class Tool:
    """Base class for all tools."""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        
    def run(self, *args, **kwargs):
        raise NotImplementedError("Tool must implement run method")

# Set up logging
logger = logging.getLogger(__name__)

class NextJsTemplateGeneratorTool(Tool):
    """
    Tool for generating Next.js project templates.
    
    This tool generates the basic file structure and configuration for a Next.js
    dashboard project, including the necessary dependencies and configuration files.
    """
    name = "nextjs_template_generator"
    description = "Generates Next.js project templates with TypeScript and Tailwind CSS"
    
    def __init__(self, output_dir: str = "./dashboard"):
        """
        Initialize the Next.js template generator tool.
        
        Args:
            output_dir: Base directory for the generated dashboard project
        """
        super().__init__(name=self.name, description=self.description)
        self.output_dir = output_dir
        logger.info(f"Next.js template generator tool initialized with output directory: {output_dir}")
    
    def run(self, query: str, **kwargs: Any) -> str:
        """
        Generate a Next.js project template based on the query.
        
        Args:
            query: JSON string containing template configuration
            **kwargs: Additional parameters
            
        Returns:
            JSON string with the paths to the generated files and directories
        """
        try:
            # Parse the query as JSON
            config = json.loads(query)
            
            # Extract configuration parameters with defaults
            project_name = config.get("project_name", "fama-dashboard")
            theme = config.get("theme", "light")
            chart_library = config.get("chart_library", "recharts")
            include_typescript = config.get("typescript", True)
            
            # Create the project directory structure
            project_dir = os.path.join(self.output_dir, project_name)
            
            # Create directories if they don't exist
            if not os.path.exists(project_dir):
                os.makedirs(project_dir)
            
            # Create directories for the Next.js project
            directories = [
                "pages",
                "pages/api",
                "components",
                "components/charts",
                "components/dashboard",
                "components/layout",
                "styles",
                "public",
                "lib",
                "hooks"
            ]
            
            created_dirs = []
            for directory in directories:
                dir_path = os.path.join(project_dir, directory)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                created_dirs.append(dir_path)
            
            # Create the package.json file
            package_json = {
                "name": project_name,
                "version": "0.1.0",
                "private": True,
                "scripts": {
                    "dev": "next dev",
                    "build": "next build",
                    "start": "next start",
                    "lint": "next lint"
                },
                "dependencies": {
                    "next": "^14.0.0",
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0"
                }
            }
            
            # Add TypeScript if requested
            if include_typescript:
                package_json["dependencies"]["typescript"] = "^5.0.0"
                package_json["dependencies"]["@types/react"] = "^18.2.0"
                package_json["dependencies"]["@types/node"] = "^20.0.0"
            
            # Add chart library
            if chart_library == "recharts":
                package_json["dependencies"]["recharts"] = "^2.8.0"
            elif chart_library == "chart.js":
                package_json["dependencies"]["chart.js"] = "^4.4.0"
                package_json["dependencies"]["react-chartjs-2"] = "^5.2.0"
            elif chart_library == "d3":
                package_json["dependencies"]["d3"] = "^7.8.0"
            
            # Add UI libraries
            package_json["dependencies"]["tailwindcss"] = "^3.3.0"
            package_json["dependencies"]["postcss"] = "^8.4.0"
            package_json["dependencies"]["autoprefixer"] = "^10.4.0"
            
            # Write package.json
            package_json_path = os.path.join(project_dir, "package.json")
            with open(package_json_path, "w") as f:
                json.dump(package_json, f, indent=2)
            
            # Create a basic Next.js configuration file
            next_config = (
                "/** @type {import('next').NextConfig} */\n"
                "const nextConfig = {\n"
                "  reactStrictMode: true,\n"
                "  swcMinify: true,\n"
                "};\n\n"
                "module.exports = nextConfig;\n"
            )
            
            next_config_path = os.path.join(project_dir, "next.config.js")
            with open(next_config_path, "w") as f:
                f.write(next_config)
            
            # Create tailwind.config.js
            tailwind_config = (
                "/** @type {import('tailwindcss').Config} */\n"
                "module.exports = {\n"
                "  content: [\n"
                "    './pages/**/*.{js,ts,jsx,tsx}',\n"
                "    './components/**/*.{js,ts,jsx,tsx}',\n"
                "  ],\n"
                "  theme: {\n"
                "    extend: {},\n"
                "  },\n"
                "  plugins: [],\n"
                "};\n"
            )
            
            tailwind_config_path = os.path.join(project_dir, "tailwind.config.js")
            with open(tailwind_config_path, "w") as f:
                f.write(tailwind_config)
            
            # Create postcss.config.js
            postcss_config = (
                "module.exports = {\n"
                "  plugins: {\n"
                "    tailwindcss: {},\n"
                "    autoprefixer: {},\n"
                "  },\n"
                "};\n"
            )
            
            postcss_config_path = os.path.join(project_dir, "postcss.config.js")
            with open(postcss_config_path, "w") as f:
                f.write(postcss_config)
            
            # Create _app.js or _app.tsx depending on TypeScript setting
            app_file_extension = "tsx" if include_typescript else "js"
            app_content = (
                "import '../styles/globals.css';\n\n"
                f"function MyApp({{ Component, pageProps }}) {{\n"
                "  return <Component {...pageProps} />;\n"
                "}\n\n"
                "export default MyApp;\n"
            )
            
            app_file_path = os.path.join(project_dir, "pages", f"_app.{app_file_extension}")
            with open(app_file_path, "w") as f:
                f.write(app_content)
            
            # Create a basic index page
            index_file_extension = "tsx" if include_typescript else "js"
            index_content = (
                "import Head from 'next/head';\n"
                "import { useState } from 'react';\n\n"
                "export default function Home() {\n"
                "  return (\n"
                "    <div className=\"min-h-screen bg-gray-100\">\n"
                "      <Head>\n"
                f"        <title>{project_name}</title>\n"
                "        <meta name=\"description\" content=\"Financial dashboard created with Fama AI\" />\n"
                "        <link rel=\"icon\" href=\"/favicon.ico\" />\n"
                "      </Head>\n\n"
                "      <main className=\"container mx-auto px-4 py-8\">\n"
                "        <h1 className=\"text-3xl font-bold text-center mb-8\">\n"
                "          Fama AI Financial Dashboard\n"
                "        </h1>\n"
                "        <div className=\"grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6\">\n"
                "          {/* Dashboard components will be added here */}\n"
                "          <div className=\"bg-white p-6 rounded-lg shadow-md\">\n"
                "            <h2 className=\"text-xl font-semibold mb-4\">Financial Metrics</h2>\n"
                "            <p>Dashboard components will be rendered here.</p>\n"
                "          </div>\n"
                "        </div>\n"
                "      </main>\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )
            
            index_file_path = os.path.join(project_dir, "pages", f"index.{index_file_extension}")
            with open(index_file_path, "w") as f:
                f.write(index_content)
            
            # Create global CSS file
            css_content = (
                "@tailwind base;\n"
                "@tailwind components;\n"
                "@tailwind utilities;\n\n"
                "body {\n"
                "  @apply bg-gray-50;\n"
                "}\n"
            )
            
            css_file_path = os.path.join(project_dir, "styles", "globals.css")
            with open(css_file_path, "w") as f:
                f.write(css_content)
            
            # Prepare response with file paths
            created_files = [
                package_json_path,
                next_config_path,
                tailwind_config_path,
                postcss_config_path,
                app_file_path,
                index_file_path,
                css_file_path
            ]
            
            result = {
                "success": True,
                "project_directory": project_dir,
                "directories_created": created_dirs,
                "files_created": created_files,
                "project_name": project_name,
                "next_steps": [
                    "Navigate to the project directory",
                    "Run 'npm install' to install dependencies",
                    "Run 'npm run dev' to start the development server"
                ]
            }
            
            logger.info(f"Next.js template generated successfully at {project_dir}")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_msg = f"Error generating Next.js template: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"success": False, "error": error_msg}, indent=2)

class ChartComponentGeneratorTool(Tool):
    """
    Tool for generating React chart components for Next.js dashboards.
    
    This tool creates visualization components for financial data using
    popular React charting libraries.
    """
    name = "chart_component_generator"
    description = "Generate React chart components for financial data visualization"
    
    def __init__(self, output_dir: str = "dashboard"):
        """
        Initialize the chart component generator tool.
        
        Args:
            output_dir: Base directory for the generated dashboard project
        """
        super().__init__(self.name, self.description)
        self.output_dir = output_dir
        logger.info(f"Chart component generator tool initialized with output directory: {output_dir}")
    
    def run(self, query: str, **kwargs: Any) -> str:
        """
        Generate a React chart component based on the query.
        
        Args:
            query: JSON string containing chart configuration
            **kwargs: Additional parameters
            
        Returns:
            JSON string with the paths to the generated files
        """
        try:
            # Parse the query as JSON
            config = json.loads(query)
            
            # Extract configuration parameters with defaults
            project_name = config.get("project_name", "fama-dashboard")
            chart_type = config.get("chart_type", "bar")
            chart_title = config.get("chart_title", "Financial Metrics")
            chart_description = config.get("chart_description", "")
            chart_library = config.get("chart_library", "recharts")
            data_structure = config.get("data_structure", {})
            include_typescript = config.get("typescript", True)
            
            # Create the project directory structure if it doesn't exist
            project_dir = os.path.join(self.output_dir, project_name)
            charts_dir = os.path.join(project_dir, "components", "charts")
            
            if not os.path.exists(charts_dir):
                os.makedirs(charts_dir)
            
            # Sanitize chart name for file naming
            component_name = "".join(
                word.capitalize() for word in chart_title.split()
            ).replace("-", "").replace("_", "")
            
            if not component_name.endswith("Chart"):
                component_name += "Chart"
            
            # Determine file extension based on TypeScript setting
            file_extension = "tsx" if include_typescript else "jsx"
            
            # Generate the chart component based on the chosen library
            if chart_library == "recharts":
                content = self._generate_recharts_component(
                    component_name, 
                    chart_type, 
                    chart_title, 
                    chart_description, 
                    data_structure,
                    include_typescript
                )
            elif chart_library == "chart.js":
                content = self._generate_chartjs_component(
                    component_name, 
                    chart_type, 
                    chart_title, 
                    chart_description, 
                    data_structure,
                    include_typescript
                )
            elif chart_library == "d3":
                content = self._generate_d3_component(
                    component_name, 
                    chart_type, 
                    chart_title, 
                    chart_description, 
                    data_structure,
                    include_typescript
                )
            else:
                return json.dumps({
                    "success": False, 
                    "error": f"Unsupported chart library: {chart_library}"
                })
            
            # Write the component file
            file_path = os.path.join(charts_dir, f"{component_name}.{file_extension}")
            with open(file_path, "w") as f:
                f.write(content)
            
            # Create an index file to export all chart components
            index_path = os.path.join(charts_dir, f"index.{file_extension}")
            
            # Check if index file exists, if not create it
            if not os.path.exists(index_path):
                with open(index_path, "w") as f:
                    f.write(f"export {{ default as {component_name} }} from './{component_name}';\n")
            else:
                # Read existing content to check if component is already exported
                with open(index_path, "r") as f:
                    index_content = f.read()
                
                # Add export statement if not already present
                export_statement = f"export {{ default as {component_name} }} from './{component_name}';"
                if export_statement not in index_content:
                    with open(index_path, "a") as f:
                        f.write(f"{export_statement}\n")
            
            result = {
                "success": True,
                "component_name": component_name,
                "component_file": file_path,
                "index_file": index_path,
                "chart_type": chart_type,
                "chart_library": chart_library,
                "usage_example": self._generate_usage_example(component_name, data_structure)
            }
            
            logger.info(f"Chart component {component_name} generated successfully at {file_path}")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_msg = f"Error generating chart component: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"success": False, "error": error_msg}, indent=2)
    
    def _generate_recharts_component(
        self, 
        component_name: str, 
        chart_type: str, 
        chart_title: str, 
        chart_description: str, 
        data_structure: Dict,
        use_typescript: bool
    ) -> str:
        """Generate a React component using Recharts library."""
        
        # Type definitions for TypeScript
        ts_imports = ""
        ts_props = ""
        
        if use_typescript:
            ts_imports = "import { ReactNode } from 'react';\n"
            
            # Generate TypeScript interfaces for the data structure
            data_items = data_structure.get("items", [])
            if data_items:
                # Extract data properties from first item to build the interface
                sample_item = data_items[0] if data_items else {}
                props_def = []
                
                for key, value in sample_item.items():
                    type_str = "string"
                    if isinstance(value, int):
                        type_str = "number"
                    elif isinstance(value, float):
                        type_str = "number"
                    elif isinstance(value, bool):
                        type_str = "boolean"
                        
                    props_def.append(f"  {key}: {type_str};")
                
                item_interface = "\n".join(props_def)
                ts_props = f"""
interface DataItem {{
{item_interface}
}}

interface {component_name}Props {{
  data: DataItem[];
  width?: number;
  height?: number;
  className?: string;
  children?: ReactNode;
}}
"""
            else:
                ts_props = f"""
interface {component_name}Props {{
  data: any[];
  width?: number;
  height?: number;
  className?: string;
  children?: ReactNode;
}}
"""
        
        # Determine the appropriate Recharts components based on chart type
        recharts_imports = "import { ResponsiveContainer, "
        chart_component = ""
        
        if chart_type == "bar":
            recharts_imports += "BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend"
            chart_component = "BarChart"
        elif chart_type == "line":
            recharts_imports += "LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend"
            chart_component = "LineChart"
        elif chart_type == "area":
            recharts_imports += "AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend"
            chart_component = "AreaChart"
        elif chart_type == "pie":
            recharts_imports += "PieChart, Pie, Cell, Tooltip, Legend"
            chart_component = "PieChart"
        else:  # Default to bar chart
            recharts_imports += "BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend"
            chart_component = "BarChart"
            
        recharts_imports += " } from 'recharts';"
        
        # Extract data field names from sample data
        data_items = data_structure.get("items", [])
        data_fields = []
        category_field = ""
        
        if data_items and len(data_items) > 0:
            # Use the first item to determine fields
            sample_item = data_items[0]
            data_fields = list(sample_item.keys())
            
            # Assume first field is category/label and rest are data
            if data_fields:
                category_field = data_fields[0]
                data_fields = data_fields[1:]
        else:
            # Default fields if no sample data provided
            category_field = "name"
            data_fields = ["value"]
        
        # Generate chart content based on chart type
        chart_content = ""
        colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff8042", "#0088fe"]
        
        if chart_type in ["bar", "line", "area"]:
            inner_content = ""
            
            for i, field in enumerate(data_fields):
                color = colors[i % len(colors)]
                
                if chart_type == "bar":
                    inner_content += f'\n          <Bar dataKey="{field}" fill="{color}" />'
                elif chart_type == "line":
                    inner_content += f'\n          <Line type="monotone" dataKey="{field}" stroke="{color}" activeDot={{ r: 8 }} />'
                elif chart_type == "area":
                    inner_content += f'\n          <Area type="monotone" dataKey="{field}" stroke="{color}" fill="{color}" fillOpacity={0.3} />'
            
            chart_content = f"""
        <ResponsiveContainer width={{width}} height={{height}}>
          <{chart_component}
            data={{data}}
            margin={{{{
              top: 20,
              right: 30,
              left: 20,
              bottom: 20,
            }}}}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="{category_field}" />
            <YAxis />
            <Tooltip />
            <Legend />{inner_content}
          </{chart_component}>
        </ResponsiveContainer>
"""
        elif chart_type == "pie":
            # Fixed version that properly escapes JSX syntax
            chart_content = f"""
        <ResponsiveContainer width={{width}} height={{height}}>
          <PieChart>
            <Pie
              data={{data}}
              cx="50%"
              cy="50%"
              labelLine={{true}}
              outerRadius={{80}}
              fill="#8884d8"
              dataKey="{data_fields[0] if data_fields else 'value'}"
              nameKey="{category_field}"
              label
            >
              {'{'}data.map((entry, index) => (
                <Cell key={{'cell-'+ index}} fill={{COLORS[index % COLORS.length]}} />
              )){'}'}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
"""
        
        # Assemble the full component
        const_colors = """
  // Custom colors for the chart
  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088fe'];
""" if chart_type == "pie" else ""

        # Create a properly formatted component template
        chart_description_paragraph = f'<p className="text-gray-500 mb-4">{chart_description}</p>' if chart_description else ''
        
        component_template = f"""import React from 'react';
{ts_imports}{recharts_imports}

{ts_props}
const {component_name} = ({{ 
  data, 
  width = '100%', 
  height = 400, 
  className = '' 
}}{': ' + component_name + 'Props' if use_typescript else ''}) => {{{const_colors}
  return (
    <div className={{`rounded-lg bg-white p-4 shadow-md ${{className}}`}}>
      <h3 className="text-lg font-semibold mb-2">{chart_title}</h3>
      {chart_description_paragraph}
{chart_content}
    </div>
  );
}};

export default {component_name};
"""
        return component_template
    
    def _generate_chartjs_component(
        self, 
        component_name: str, 
        chart_type: str, 
        chart_title: str, 
        chart_description: str, 
        data_structure: Dict,
        use_typescript: bool
    ) -> str:
        """Generate a React component using Chart.js library."""
        
        # Type definitions for TypeScript
        ts_imports = ""
        ts_props = ""
        
        if use_typescript:
            ts_imports = "import { ReactNode } from 'react';\n"
            
            # Generate TypeScript interfaces for the data structure
            data_items = data_structure.get("items", [])
            if data_items:
                # Extract data properties from first item to build the interface
                sample_item = data_items[0] if data_items else {}
                props_def = []
                
                for key, value in sample_item.items():
                    type_str = "string"
                    if isinstance(value, int):
                        type_str = "number"
                    elif isinstance(value, float):
                        type_str = "number"
                    elif isinstance(value, bool):
                        type_str = "boolean"
                        
                    props_def.append(f"  {key}: {type_str};")
                
                item_interface = "\n".join(props_def)
                ts_props = f"""
interface DataItem {{
{item_interface}
}}

interface {component_name}Props {{
  data: DataItem[];
  width?: number | string;
  height?: number | string;
  className?: string;
  children?: ReactNode;
}}
"""
            else:
                ts_props = f"""
interface {component_name}Props {{
  data: any[];
  width?: number | string;
  height?: number | string;
  className?: string;
  children?: ReactNode;
}}
"""
        
        # Imports for Chart.js
        chartjs_imports = "import { "
        
        if chart_type == "bar":
            chartjs_imports += "Bar"
            chart_component = "Bar"
        elif chart_type == "line":
            chartjs_imports += "Line"
            chart_component = "Line"
        elif chart_type == "pie":
            chartjs_imports += "Pie"
            chart_component = "Pie"
        elif chart_type == "doughnut":
            chartjs_imports += "Doughnut"
            chart_component = "Doughnut"
        else:  # Default to bar chart
            chartjs_imports += "Bar"
            chart_component = "Bar"
            
        chartjs_imports += " } from 'react-chartjs-2';"
        
        # Chart.js requires additional imports for the chart components to work
        chartjs_registry = """import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);
"""
        
        # Extract data field names from sample data
        data_items = data_structure.get("items", [])
        data_fields = []
        labels = []
        
        if data_items and len(data_items) > 0:
            # Use the first item to determine fields
            sample_item = data_items[0]
            data_fields = list(sample_item.keys())
            
            # Assume first field is category/label and rest are data
            if data_fields:
                labels = [item.get(data_fields[0], "") for item in data_items]
                data_fields = data_fields[1:]
        else:
            # Default fields if no sample data provided
            labels = ["Category 1", "Category 2", "Category 3"]
            data_fields = ["value"]
            
        # Generate dataset preparation code
        if chart_type in ["bar", "line"]:
            datasets_code = f"""
  // Convert data to Chart.js format
  const labels = data.map(item => item.{data_fields[0] if not data_fields else "category"});
  
  const datasets = [
"""
            
            colors = ["rgba(75, 192, 192, 0.6)", "rgba(54, 162, 235, 0.6)", "rgba(255, 206, 86, 0.6)", "rgba(255, 99, 132, 0.6)"]
            
            for i, field in enumerate(data_fields):
                color = colors[i % len(colors)]
                border_color = color.replace("0.6", "1")
                
                datasets_code += f"""    {{
      label: '{field.replace("_", " ").title()}',
      data: data.map(item => item.{field}),
      backgroundColor: '{color}',
      borderColor: '{border_color}',
      borderWidth: 1,
    }},
"""
            
            datasets_code += "  ];"
            
        elif chart_type in ["pie", "doughnut"]:
            datasets_code = f"""
  // Convert data to Chart.js format
  const labels = data.map(item => item.{data_fields[0] if not data_fields else "category"});
  
  const backgroundColor = [
    'rgba(75, 192, 192, 0.6)',
    'rgba(54, 162, 235, 0.6)',
    'rgba(255, 206, 86, 0.6)',
    'rgba(255, 99, 132, 0.6)',
    'rgba(153, 102, 255, 0.6)',
  ];
  
  const datasets = [
    {{
      data: data.map(item => item.{data_fields[0] if data_fields else "value"}),
      backgroundColor,
      borderColor: backgroundColor.map(color => color.replace('0.6', '1')),
      borderWidth: 1,
    }},
  ];
"""
        
        # Assemble the chart options and data
        chart_data = f"""
  const chartData = {{
    labels,
    datasets,
  }};
"""
        
        chart_options = f"""
  const options = {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{
        position: 'top',
      }},
      title: {{
        display: true,
        text: '{chart_title}',
      }},
    }},
  }};
"""
        
        # Create a properly formatted component template
        chart_description_paragraph = f'<p className="text-gray-500 mb-4">{chart_description}</p>' if chart_description else ''
        
        component_template = f"""import React from 'react';
{ts_imports}{chartjs_imports}
{chartjs_registry}
{ts_props}
const {component_name} = ({{ 
  data, 
  width = '100%', 
  height = 400, 
  className = '' 
}}{': ' + component_name + 'Props' if use_typescript else ''}) => {{
{datasets_code}
{chart_data}
{chart_options}

  return (
    <div className={{`rounded-lg bg-white p-4 shadow-md ${{className}}`}}>
      <h3 className="text-lg font-semibold mb-2">{chart_title}</h3>
      {chart_description_paragraph}
      <div style={{ width, height }}>
        <{chart_component} data={{chartData}} options={{options}} />
      </div>
    </div>
  );
}};

export default {component_name};
"""
        return component_template
    
    def _generate_d3_component(
        self, 
        component_name: str, 
        chart_type: str, 
        chart_title: str, 
        chart_description: str, 
        data_structure: Dict,
        use_typescript: bool
    ) -> str:
        """Generate a React component using D3 library."""
        
        # D3 components are more complex, so only implement a basic bar chart for now
        ts_interface = ""
        if use_typescript:
            ts_interface = f"""interface {component_name}Props {{
  data: any[];
  width?: number | string;
  height?: number;
  className?: string;
}}

"""
        
        ts_type_annotation = ""
        if use_typescript:
            ts_type_annotation = f": {component_name}Props"
            
        svg_ref_type = ""
        if use_typescript:
            svg_ref_type = "<SVGSVGElement>"
            
        chart_desc_paragraph = ""
        if chart_description:
            chart_desc_paragraph = f'<p className="text-gray-500 mb-4">{chart_description}</p>'
        
        component_template = f"""import React, {{ useRef, useEffect }} from 'react';
import * as d3 from 'd3';

{ts_interface}const {component_name} = ({{ 
  data, 
  width = '100%', 
  height = 400,
  className = '',
}}{ts_type_annotation}) => {{
  const svgRef = useRef{svg_ref_type}(null);

  useEffect(() => {{
    if (!data || !data.length || !svgRef.current) return;

    // Clear any existing chart
    d3.select(svgRef.current).selectAll('*').remove();

    // Setup dimensions
    const margin = {{ top: 20, right: 30, bottom: 40, left: 60 }};
    const innerWidth = typeof width === 'number' ? width : 600;
    const innerHeight = height - margin.top - margin.bottom;
    const chartWidth = innerWidth - margin.left - margin.right;

    // Create SVG
    const svg = d3
      .select(svgRef.current)
      .attr('width', innerWidth)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${{margin.left}},${{margin.top}})`);

    // X scale
    const x = d3
      .scaleBand()
      .domain(data.map(d => d.name || d.category || ''))
      .range([0, chartWidth])
      .padding(0.2);

    // Y scale
    const y = d3
      .scaleLinear()
      .domain([0, d3.max(data, d => d.value || 0) * 1.1])
      .range([innerHeight, 0]);

    // Add X axis
    svg
      .append('g')
      .attr('transform', `translate(0,${{innerHeight}}`)
      .call(d3.axisBottom(x))
      .selectAll('text')
      .attr('transform', 'translate(-10,0)rotate(-45)')
      .style('text-anchor', 'end');

    // Add Y axis
    svg.append('g').call(d3.axisLeft(y));

    // Add bars
    svg
      .selectAll('rect')
      .data(data)
      .enter()
      .append('rect')
      .attr('x', d => x(d.name || d.category || ''))
      .attr('y', d => y(d.value || 0))
      .attr('width', x.bandwidth())
      .attr('height', d => innerHeight - y(d.value || 0))
      .attr('fill', '#4F46E5');
      
    // Add title
    svg
      .append('text')
      .attr('x', chartWidth / 2)
      .attr('y', -margin.top / 2)
      .attr('text-anchor', 'middle')
      .style('font-size', '16px')
      .style('font-weight', 'bold')
      .text('{chart_title}');
  }}, [data, width, height]);

  return (
    <div className={{`rounded-lg bg-white p-4 shadow-md ${{className}}`}}>
      <h3 className="text-lg font-semibold mb-2">{chart_title}</h3>
      {chart_desc_paragraph}
      <svg ref={{svgRef}} style={{ maxWidth: '100%' }}></svg>
    </div>
  );
}};

export default {component_name};
"""
    
    def _generate_usage_example(self, component_name: str, data_structure: Dict) -> str:
        """Generate a usage example for the created component."""
        data_items = data_structure.get("items", [])
        
        # If no data structure provided, create a sample one
        if not data_items:
            data_items = [
                {"name": "Category 1", "value": 400},
                {"name": "Category 2", "value": 300},
                {"name": "Category 3", "value": 200},
                {"name": "Category 4", "value": 100},
            ]
        
        data_string = json.dumps(data_items, indent=2).replace('"', "'")
        
        example_usage = f"""
// Example usage of {component_name}:
import {{ {component_name} }} from './components/charts';

// Your data
const data = {data_string};

export default function YourComponent() {{
  return (
    <div>
      <{component_name} data={{data}} />
    </div>
  );
}}
"""
        return example_usage 